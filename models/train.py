"""
Mask R-CNN Training Module
==========================
Handles dataset loading, optimizer initialization, learning rate scheduling,
and the main epoch loops for training and validation.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torchvision
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.mask_rcnn import ScrewDataset, get_model, get_transforms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def collate_fn(batch):
    """Custom collate function for DataLoader to handle target dicts."""
    return tuple(zip(*batch))


def train_one_epoch(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    data_loader: DataLoader,
    device: torch.device,
    epoch: int,
    print_freq: int = 10,
) -> float:
    """Train the model for one epoch."""
    model.train()
    epoch_loss = 0.0
    
    for i, (images, targets) in enumerate(data_loader):
        # Move images and targets to target device
        images = list(image.to(device) for image in images)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        # Forward pass
        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())

        # Backward pass
        optimizer.zero_grad()
        losses.backward()
        optimizer.step()

        epoch_loss += losses.item()

        if i % print_freq == 0:
            loss_str = ", ".join([f"{k}: {v.item():.4f}" for k, v in loss_dict.items()])
            logger.info(
                f"Epoch [{epoch}] Batch [{i}/{len(data_loader)}] "
                f"Total Loss: {losses.item():.4f} ({loss_str})"
            )

    avg_loss = epoch_loss / len(data_loader)
    logger.info(f"Epoch [{epoch}] Average Train Loss: {avg_loss:.4f}")
    return avg_loss


@torch.no_grad()
def validate(
    model: torch.nn.Module,
    data_loader: DataLoader,
    device: torch.device,
) -> float:
    """
    Compute validation loss.
    Note: PyTorch Torchvision Mask R-CNN only computes loss when model is in train() mode.
    Therefore we set model to train() mode but disable gradients.
    """
    model.train()  # Crucial to get loss dict
    val_loss = 0.0
    
    for images, targets in data_loader:
        images = list(image.to(device) for image in images)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())
        val_loss += losses.item()

    avg_val_loss = val_loss / len(data_loader)
    logger.info(f"Validation Average Loss: {avg_val_loss:.4f}")
    return avg_val_loss


def train_model(config: Dict) -> None:
    """Execute training pipeline."""
    # Setup directories
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Device auto-detection
    device = torch.device("cpu")
    logger.info("Using CPU")

    # Load datasets
    train_dataset = ScrewDataset(
        root_dir=Path(config["data_dir"]) / "train" / "images",
        annotation_file=config["train_ann"],
        transforms=get_transforms(train=True)
    )
    val_dataset = ScrewDataset(
        root_dir=Path(config["data_dir"]) / "train" / "images",
        annotation_file=config["val_ann"],
        transforms=get_transforms(train=False)
    )

    # Dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=config.get("num_workers", 0),
        collate_fn=collate_fn
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config["batch_size"],
        shuffle=False,
        num_workers=config.get("num_workers", 0),
        collate_fn=collate_fn
    )

    # Model, Optimizer, Scheduler
    model = get_model(num_classes=2, pretrained=True)
    model.to(device)

    # Fine-tune only heads or train everything depending on dataset size
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=config["lr"], weight_decay=0.0005)
    
    # Scheduler: Cosine Annealing
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config["epochs"]
    )

    # Metrics logging
    history = {"train_loss": [], "val_loss": [], "lr": []}
    best_val_loss = float("inf")

    # Start training loop
    start_time = time.time()
    for epoch in range(1, config["epochs"] + 1):
        epoch_start = time.time()
        
        # Train & Val
        train_loss = train_one_epoch(model, optimizer, train_loader, device, epoch)
        val_loss = validate(model, val_loader, device)

        # Step learning rate
        scheduler.step()

        # Log metrics
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["lr"].append(optimizer.param_groups[0]["lr"])

        # Checkpoint saving
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            # Save weights
            torch.save(
                model.state_dict(),
                output_dir / "best_model.pth"
            )
            logger.info(f"  [CHECKPOINT] New best model saved (Val Loss: {val_loss:.4f})")

        # Regular saving
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "history": history,
            },
            output_dir / "checkpoint_latest.pth"
        )

        epoch_dur = time.time() - epoch_start
        logger.info(f"Epoch [{epoch}] completed in {epoch_dur:.1f}s")

    total_time = time.time() - start_time
    logger.info(f"Training finished in {total_time/60:.2f} minutes.")

    # Save log file
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(history, f, indent=4)

    # Plot loss curves
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, len(history["train_loss"]) + 1), history["train_loss"], label="Train Loss")
    plt.plot(range(1, len(history["val_loss"]) + 1), history["val_loss"], label="Val Loss")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Mask R-CNN Training Curves")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "loss_curves.png")
    plt.close()
    logger.info(f"Loss curves saved to {output_dir / 'loss_curves.png'}")


def main():
    parser = argparse.ArgumentParser(description="Train Mask R-CNN for Screw Segmentation.")
    parser.add_argument("--data-dir", type=str, default="dataset", help="Root dataset directory.")
    parser.add_argument("--train-ann", type=str, required=True, help="Train annotation JSON.")
    parser.add_argument("--val-ann", type=str, required=True, help="Val annotation JSON.")
    parser.add_argument("--epochs", type=int, default=80, help="Number of epochs.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size.")
    parser.add_argument("--lr", type=float, default=0.0001, help="Learning rate.")
    parser.add_argument("--output-dir", type=str, default="models/weights", help="Where to save checkpoints.")
    parser.add_argument("--num-workers", type=int, default=0, help="Number of CPU workers for dataloader.")

    args = parser.parse_args()

    config = vars(args)
    train_model(config)


if __name__ == "__main__":
    main()
