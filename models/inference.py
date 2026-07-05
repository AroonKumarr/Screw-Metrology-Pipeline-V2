"""
Mask R-CNN Inference Module
===========================
Executes instance segmentation on new images using a trained model.
Returns segmentation masks, bounding boxes, and confidence scores.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

import torch
import numpy as np
import cv2
from PIL import Image
import torchvision

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.mask_rcnn import get_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_model(
    model_path: Union[str, Path],
    num_classes: int = 2,
    device: Union[str, torch.device, None] = None,
) -> Tuple[torch.nn.Module, torch.device]:
    """
    Load a trained Mask R-CNN model.

    Parameters
    ----------
    model_path : str or Path
        Path to the trained .pth model file.
    num_classes : int
        Number of classes. Default 2.
    device : str or torch.device, optional
        Device to load model on.

    Returns
    -------
    Tuple[torch.nn.Module, torch.device]
        Loaded model and device.
    """
    device = torch.device("cpu")

    model = get_model(num_classes=num_classes, pretrained=False)
    
    # Load state dict
    state_dict = torch.load(str(model_path), map_location=device)
    # Handle if state dict is wrapped in a checkpoint dict
    if "model_state_dict" in state_dict:
        state_dict = state_dict["model_state_dict"]
        
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    logger.info(f"Loaded Mask R-CNN model weights from {model_path} onto {device}")
    return model, device


def predict(
    model: torch.nn.Module,
    image: Union[np.ndarray, Image.Image],
    device: torch.device,
    confidence_threshold: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run Mask R-CNN model on a single input image.

    Parameters
    ----------
    model : torch.nn.Module
        Trained model in eval mode.
    image : np.ndarray or Image.Image
        Input image.
    device : torch.device
        Target device.
    confidence_threshold : float
        Filter results with score below this value.

    Returns
    -------
    Tuple
        - masks (binary masks as np.ndarray [N, H, W], values 0 or 1)
        - boxes (bounding boxes [N, 4] formatted [xmin, ymin, xmax, ymax])
        - scores (confidence scores [N])
    """
    # Convert image to PIL if it is NumPy
    if isinstance(image, np.ndarray):
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # OpenCV loads as BGR
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
        else:
            pil_image = Image.fromarray(image)
    else:
        pil_image = image

    orig_w, orig_h = pil_image.size
    scale = min(512.0 / max(orig_w, orig_h), 1.0)
    if scale < 1.0:
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        pil_image_resized = pil_image.resize((new_w, new_h), Image.BILINEAR)
    else:
        pil_image_resized = pil_image

    # Convert to tensor and normalize [0, 1]
    transform = torchvision.transforms.ToTensor()
    img_tensor = transform(pil_image_resized).to(device)

    with torch.no_grad():
        prediction = model([img_tensor])[0]

    # Move to CPU
    scores = prediction["scores"].cpu().numpy()
    boxes = prediction["boxes"].cpu().numpy()
    masks = prediction["masks"].cpu().numpy()  # shape: [N, 1, H, W]

    # Filter by confidence
    keep = scores >= confidence_threshold
    scores = scores[keep]
    boxes = boxes[keep]
    masks = masks[keep]

    # Scale boxes back to original size
    if len(boxes) > 0:
        boxes = boxes / scale

    # Convert masks to binary numpy array [N, H, W] and scale back
    if len(masks) > 0:
        masks = (masks.squeeze(1) > 0.5).astype(np.uint8)
        resized_masks = []
        for m in masks:
            if scale < 1.0:
                pil_m = Image.fromarray(m)
                pil_m = pil_m.resize((orig_w, orig_h), Image.NEAREST)
                resized_masks.append(np.array(pil_m))
            else:
                resized_masks.append(m)
        masks = np.array(resized_masks)
    else:
        masks = np.zeros((0, orig_h, orig_w), dtype=np.uint8)

    return masks, boxes, scores


def visualize_prediction(
    image: np.ndarray,
    masks: np.ndarray,
    boxes: np.ndarray,
    scores: np.ndarray,
    output_path: Union[str, Path, None] = None,
) -> np.ndarray:
    """
    Generate mask overlay and bounding boxes on the image.

    Parameters
    ----------
    image : np.ndarray
        Original input image (BGR).
    masks : np.ndarray
        Binary segmentation masks [N, H, W].
    boxes : np.ndarray
        Bounding boxes [N, 4].
    scores : np.ndarray
        Prediction scores [N].
    output_path : str or Path, optional
        Path to save the resulting image.

    Returns
    -------
    np.ndarray
        Visualized image with overlays.
    """
    vis_img = image.copy()
    num_objects = len(masks)

    # Apply masks
    mask_overlay = np.zeros_like(image, dtype=np.uint8)
    for i in range(num_objects):
        mask = masks[i]
        # Draw mask as semi-transparent red
        mask_overlay[mask > 0] = [0, 0, 255]

    # Blend original and mask overlay
    if num_objects > 0:
        cv2.addWeighted(mask_overlay, 0.4, vis_img, 0.6, 0, vis_img)

    # Draw boxes and labels
    for i in range(num_objects):
        box = boxes[i].astype(int)
        score = scores[i]
        
        # Bounding box
        cv2.rectangle(vis_img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        
        # Text background
        label = f"Screw: {score:.2%}"
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            vis_img,
            (box[0], box[1] - text_height - 10),
            (box[0] + text_width + 10, box[1]),
            (0, 255, 0),
            -1
        )
        # Text label
        cv2.putText(
            vis_img,
            label,
            (box[0] + 5, box[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), vis_img)
        logger.info(f"Saved prediction visualization: {output_path}")

    return vis_img


def run_inference(
    model_path: str,
    input_path: str,
    output_dir: str,
    confidence_threshold: float = 0.5,
) -> None:
    """Run inference pipeline on a file or directory."""
    model, device = load_model(model_path)

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    
    if input_path.is_dir():
        image_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    else:
        image_files = [input_path]

    for img_path in image_files:
        from PIL import Image, ImageOps
        try:
            pil_img = Image.open(str(img_path)).convert("RGB")
            pil_img = ImageOps.exif_transpose(pil_img)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.warning(f"Could not load image {img_path}: {e}")
            continue

        masks, boxes, scores = predict(model, img, device, confidence_threshold)
        logger.info(f"Detected {len(masks)} screws in {img_path.name}")

        out_vis_path = output_dir / f"pred_{img_path.name}"
        visualize_prediction(img, masks, boxes, scores, out_vis_path)


def main():
    parser = argparse.ArgumentParser(description="Run Mask R-CNN inference on new images.")
    parser.add_argument("--model", type=str, required=True, help="Trained .pth weights file.")
    parser.add_argument("--input", type=str, required=True, help="Single image or image directory.")
    parser.add_argument("--output-dir", type=str, default="outputs/predictions", help="Output save directory.")
    parser.add_argument("--confidence", type=float, default=0.5, help="Confidence threshold (default: 0.5).")

    args = parser.parse_args()

    run_inference(
        model_path=args.model,
        input_path=args.input,
        output_dir=args.output_dir,
        confidence_threshold=args.confidence
    )


if __name__ == "__main__":
    main()
