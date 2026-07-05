"""
Mask R-CNN Evaluation Module
============================
Evaluates a trained model on the test dataset split.
Computes mAP, precision, recall, F1, and Intersection over Union (IoU) metrics.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import torch
import torchvision
import numpy as np
import cv2
import matplotlib.pyplot as plt
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.mask_rcnn import ScrewDataset, get_model, get_transforms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def compute_iou(mask1: np.ndarray, mask2: np.ndarray) -> float:
    """Compute Intersection over Union (IoU) between two binary masks."""
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    if union == 0:
        return 0.0
    return float(intersection / union)


def compute_metrics(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5,
) -> Dict:
    """
    Compute classification/segmentation metrics (Precision, Recall, F1, average IoU).
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0
    ious = []

    for pred, gt in zip(predictions, ground_truths):
        pred_masks = pred["masks"]  # binary masks [N, H, W]
        gt_masks = gt["masks"]      # binary masks [M, H, W]

        num_pred = len(pred_masks)
        num_gt = len(gt_masks)

        if num_pred == 0:
            total_fn += num_gt
            continue
        if num_gt == 0:
            total_fp += num_pred
            continue

        # Compute IoU matrix between all pred and gt masks
        iou_matrix = np.zeros((num_pred, num_gt))
        for p_idx in range(num_pred):
            for g_idx in range(num_gt):
                iou_matrix[p_idx, g_idx] = compute_iou(pred_masks[p_idx], gt_masks[g_idx])

        # Match predictions to ground truth
        matched_gt = set()
        matched_pred = set()
        
        # Sort matches by IoU score
        matches = []
        for p_idx in range(num_pred):
            for g_idx in range(num_gt):
                matches.append((iou_matrix[p_idx, g_idx], p_idx, g_idx))
        matches.sort(reverse=True, key=lambda x: x[0])

        for score, p_idx, g_idx in matches:
            if p_idx not in matched_pred and g_idx not in matched_gt:
                if score >= iou_threshold:
                    matched_pred.add(p_idx)
                    matched_gt.add(g_idx)
                    ious.append(score)

        tp = len(matched_pred)
        fp = num_pred - tp
        fn = num_gt - tp

        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    mean_iou = float(np.mean(ious)) if ious else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "mean_iou": mean_iou,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
    }


def evaluate_model(
    model_path: str,
    test_dir: str,
    annotation_file: str,
    output_dir: str,
    device: Optional[torch.device] = None,
) -> Dict:
    """Run model on test split and compute accuracy metrics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    vis_dir = output_dir / "predictions"
    vis_dir.mkdir(parents=True, exist_ok=True)

    # Device
    if device is None:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

    # Load dataset
    test_dataset = ScrewDataset(
        root_dir=test_dir,
        annotation_file=annotation_file,
        transforms=get_transforms(train=False)
    )

    # Load model
    model = get_model(num_classes=2, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    logger.info(f"Loaded model weights from {model_path}")
    logger.info(f"Evaluating on {len(test_dataset)} test samples...")

    predictions = []
    ground_truths = []

    with torch.no_grad():
        for i in tqdm(range(len(test_dataset)), desc="Inference"):
            image_tensor, target = test_dataset[i]
            
            # Predict
            pred = model([image_tensor.to(device)])[0]
            
            # Filter predictions with confidence >= 0.5
            scores = pred["scores"].cpu().numpy()
            keep = scores >= 0.5
            
            pred_masks_tensor = pred["masks"][keep] > 0.5
            pred_masks = pred_masks_tensor.squeeze(1).cpu().numpy().astype(np.uint8)
            
            predictions.append({
                "masks": pred_masks,
                "boxes": pred["boxes"][keep].cpu().numpy(),
                "scores": scores[keep]
            })

            # Ground Truth
            gt_masks = target["masks"].cpu().numpy().astype(np.uint8)
            ground_truths.append({
                "masks": gt_masks,
                "boxes": target["boxes"].cpu().numpy()
            })

            # Save sample visualizations (up to 10 images)
            if i < 10:
                # Load raw original image for saving
                img_path = test_dataset.root_dir / test_dataset.coco.loadImgs(test_dataset.ids[i])[0]["file_name"]
                if not img_path.exists():
                    img_path = test_dataset.root_dir / Path(img_path).name
                from PIL import Image, ImageOps
                try:
                    pil_img = Image.open(str(img_path)).convert("RGB")
                    pil_img = ImageOps.exif_transpose(pil_img)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    img = None
                
                if img is not None:
                    # Resize original image to match mask resolution for visualization overlay
                    mask_h, mask_w = img.shape[:2]
                    if len(gt_masks) > 0:
                        mask_h, mask_w = gt_masks.shape[1:]
                    elif len(pred_masks) > 0:
                        mask_h, mask_w = pred_masks.shape[1:]
                    img = cv2.resize(img, (mask_w, mask_h))
                    h, w = img.shape[:2]
                    
                    # Create masks overlay
                    overlay_gt = img.copy()
                    for m in gt_masks:
                        overlay_gt[m > 0] = [0, 255, 0]  # Green for Ground Truth
                    
                    overlay_pred = img.copy()
                    for m in pred_masks:
                        overlay_pred[m > 0] = [0, 0, 255]  # Red for Prediction
                        
                    # alpha blend
                    cv2.addWeighted(overlay_gt, 0.4, img, 0.6, 0, overlay_gt)
                    cv2.addWeighted(overlay_pred, 0.4, img, 0.6, 0, overlay_pred)
                    
                    # Create 3-pane comparison plot
                    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                    axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    axes[0].set_title("Input Image")
                    axes[0].axis("off")
                    
                    axes[1].imshow(cv2.cvtColor(overlay_gt, cv2.COLOR_BGR2RGB))
                    axes[1].set_title("Ground Truth Mask")
                    axes[1].axis("off")
                    
                    axes[2].imshow(cv2.cvtColor(overlay_pred, cv2.COLOR_BGR2RGB))
                    axes[2].set_title("Predicted Mask (Conf >= 0.5)")
                    axes[2].axis("off")
                    
                    plt.tight_layout()
                    plt.savefig(vis_dir / f"test_val_{img_path.name}")
                    plt.close()

    # Calculate metrics
    metrics = compute_metrics(predictions, ground_truths, iou_threshold=0.5)

    # Compute mAP at thresholds 0.5 to 0.95
    map_scores = []
    for thresh in np.arange(0.5, 1.0, 0.05):
        m = compute_metrics(predictions, ground_truths, iou_threshold=thresh)
        map_scores.append(m["precision"])  # simplified precision-recall AP

    metrics["mAP_0.5"] = metrics["precision"]
    metrics["mAP_0.5_0.95"] = float(np.mean(map_scores))

    logger.info("Evaluation metrics computed:")
    for k, v in metrics.items():
        if isinstance(v, float):
            logger.info(f"  {k:15}: {v:.4f}")
        else:
            logger.info(f"  {k:15}: {v}")

    # Save to metrics.json
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    # Save Markdown report
    generate_evaluation_report(metrics, output_dir)

    return metrics


def generate_evaluation_report(metrics: Dict, output_dir: Path) -> None:
    """Save clean evaluation report in MD format."""
    report_content = f"""# Model Training and Evaluation Report

## Test Set Performance Summary
Below are the metrics computed on the held-out test split (10% of dataset).

| Metric | Target Value | Model Score | Evaluation |
|--------|--------------|-------------|------------|
| **Precision** | > 0.85 | {metrics['precision']:.4f} | {"Pass" if metrics['precision'] > 0.85 else "Need Tuning"} |
| **Recall** | > 0.85 | {metrics['recall']:.4f} | {"Pass" if metrics['recall'] > 0.85 else "Need Tuning"} |
| **F1-Score** | > 0.85 | {metrics['f1_score']:.4f} | {"Pass" if metrics['f1_score'] > 0.85 else "Need Tuning"} |
| **Mean IoU** | > 0.70 | {metrics['mean_iou']:.4f} | {"Pass" if metrics['mean_iou'] > 0.70 else "Need Tuning"} |
| **mAP@0.5** | - | {metrics['mAP_0.5']:.4f} | - |
| **mAP@0.5:0.95** | - | {metrics['mAP_0.5_0.95']:.4f} | - |

## Dataset Quantities
- **True Positives (TP)**: {metrics['true_positives']}
- **False Positives (FP)**: {metrics['false_positives']}
- **False Negatives (FN)**: {metrics['false_negatives']}

---
*Report generated automatically by Mask R-CNN Evaluation Module.*
"""
    with open(output_dir / "evaluation_report.md", "w") as f:
        f.write(report_content)
    logger.info(f"Saved report: {output_dir / 'evaluation_report.md'}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Mask R-CNN model on Test split.")
    parser.add_argument("--model", type=str, required=True, help="Path to best_model.pth.")
    parser.add_argument("--test-dir", type=str, required=True, help="Directory of test images.")
    parser.add_argument("--test-ann", type=str, required=True, help="Test COCO annotation JSON.")
    parser.add_argument("--output-dir", type=str, default="outputs/metrics", help="Directory to save output metrics.")

    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        test_dir=args.test_dir,
        annotation_file=args.test_ann,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
