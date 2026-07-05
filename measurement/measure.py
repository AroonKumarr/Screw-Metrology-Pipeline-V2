"""
Inference & Metrology Module
============================
Integrates camera undistortion, Mask R-CNN segmentation, reference object detection,
and metric conversion to measure a screw in real-world millimetres.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
import pandas as pd
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calibration.undistort import load_calibration, undistort_image
from models.inference import load_model, predict
from measurement.reference_detector import detect_reference, draw_markers
from measurement.pixel_to_mm import measure_object_mm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def measure_screw(
    image_path: Union[str, Path],
    model_path: Union[str, Path],
    calibration_dir: Optional[Union[str, Path]] = None,
    marker_size_mm: float = 20.0,
    confidence_threshold: float = 0.7,
    device: Optional[torch.device] = None,
) -> Dict:
    """
    Run end-to-end screw measurement pipeline on a single image.

    Parameters
    ----------
    image_path : str or Path
        Path to input image file.
    model_path : str or Path
        Path to trained Mask R-CNN weights.
    calibration_dir : str or Path, optional
        Directory with camera calibration matrices.
    marker_size_mm : float
        Physical width/height of the reference ArUco marker in mm (default: 20.0).
    confidence_threshold : float
        Inference score threshold.
    device : torch.device, optional
        Target hardware.

    Returns
    -------
    Dict
        Dictionary containing metric measurements, mask arrays, confidence,
        and annotated visualization.
    """
    image_path = Path(image_path)
    from PIL import Image, ImageOps
    pil_img = Image.open(str(image_path)).convert("RGB")
    pil_img = ImageOps.exif_transpose(pil_img)
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Step 1: Undistort if calibration is provided
    if calibration_dir:
        camera_matrix, dist_coeffs = load_calibration(calibration_dir)
        processed_img = undistort_image(img, camera_matrix, dist_coeffs)
        logger.info("Undistorted input image using camera calibration parameters.")
    else:
        processed_img = img.copy()
        logger.warning("No camera calibration provided. Proceeding with raw image.")

    # Step 2: Detect reference ArUco marker
    ref_info = detect_reference(processed_img, known_marker_size_mm=marker_size_mm)
    pixels_per_mm = ref_info["pixels_per_mm"]

    # Step 3: Load Mask R-CNN model & run prediction
    model, target_device = load_model(model_path, device=device)
    masks, boxes, scores = predict(
        model, processed_img, target_device, confidence_threshold=confidence_threshold
    )

    if len(masks) == 0:
        raise ValueError(
            f"No screws detected in {image_path.name} above the confidence "
            f"threshold of {confidence_threshold:.2%}."
        )

    # For metrology, we take the highest-confidence prediction
    best_idx = np.argmax(scores)
    screw_mask = masks[best_idx]
    screw_score = scores[best_idx]

    # Step 4: Convert pixel dimensions to mm
    metric_results = measure_object_mm(screw_mask, pixels_per_mm)

    # Step 5: Draw visualization overlays
    annotated = visualize_measurement(
        processed_img, screw_mask, metric_results, ref_info, screw_score
    )

    return {
        "width_mm": metric_results["width_mm"],
        "height_mm": metric_results["height_mm"],
        "confidence": float(screw_score),
        "width_px": metric_results["width_px"],
        "height_px": metric_results["height_px"],
        "pixels_per_mm": pixels_per_mm,
        "num_screws_detected": len(masks),
        "mask": screw_mask,
        "annotated_image": annotated,
    }


def visualize_measurement(
    image: np.ndarray,
    mask: np.ndarray,
    measure_res: Dict,
    ref_info: Dict,
    confidence: float,
) -> np.ndarray:
    """Generate professional metrology overlay."""
    vis_img = image.copy()

    # Draw detected ArUco reference marker
    vis_img = draw_markers(vis_img, ref_info["marker_corners"], ref_info["marker_ids"])

    # Draw semi-transparent green mask overlay on the screw
    mask_overlay = np.zeros_like(vis_img, dtype=np.uint8)
    mask_overlay[mask > 0] = [0, 255, 0]  # Green mask
    cv2.addWeighted(mask_overlay, 0.3, vis_img, 0.7, 0, vis_img)

    # Get rotated rect points
    box_points = cv2.boxPoints(measure_res["rect"]).astype(int)
    cv2.drawContours(vis_img, [box_points], 0, (255, 0, 0), 2)  # Blue rectangle

    # Extract info for drawing measurement annotations
    center = tuple(map(int, measure_res["center"]))
    width_mm = measure_res["width_mm"]
    height_mm = measure_res["height_mm"]

    # Show values on the image
    cv2.circle(vis_img, center, 4, (0, 0, 255), -1)  # Red center point

    # Draw dimension labels
    # Bounding Box corners
    pt0, pt1, pt2, pt3 = box_points
    
    # Height (length line)
    mid_h1 = ((pt0[0] + pt1[0]) // 2, (pt0[1] + pt1[1]) // 2)
    mid_h2 = ((pt2[0] + pt3[0]) // 2, (pt2[1] + pt3[1]) // 2)
    cv2.line(vis_img, mid_h1, mid_h2, (0, 255, 255), 2)  # Yellow height line
    
    # Width (diameter line)
    mid_w1 = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
    mid_w2 = ((pt3[0] + pt0[0]) // 2, (pt3[1] + pt0[1]) // 2)
    cv2.line(vis_img, mid_w1, mid_w2, (0, 255, 255), 2)  # Yellow width line

    # Create info card background
    info_x, info_y = 30, 50
    card_w, card_h = 320, 140
    overlay = vis_img.copy()
    cv2.rectangle(
        overlay,
        (info_x, info_y),
        (info_x + card_w, info_y + card_h),
        (0, 0, 0),
        -1
    )
    cv2.addWeighted(overlay, 0.6, vis_img, 0.4, 0, vis_img)

    # Info card text labels
    labels = [
        "METROLOGY RESULTS",
        f"Object    : Phillips Screw",
        f"Length    : {height_mm:.2f} mm",
        f"Diameter  : {width_mm:.2f} mm",
        f"Confidence: {confidence:.2%}",
    ]

    for idx, text in enumerate(labels):
        color = (0, 255, 255) if idx == 0 else (255, 255, 255)
        scale = 0.6 if idx == 0 else 0.5
        thickness = 2 if idx == 0 else 1
        cv2.putText(
            vis_img,
            text,
            (info_x + 15, info_y + 25 + (idx * 23)),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA
        )

    return vis_img


def batch_measure(
    image_dir: str,
    model_path: str,
    output_dir: str,
    calibration_dir: Optional[str] = None,
    marker_size_mm: float = 20.0,
    confidence_threshold: float = 0.7,
) -> List[Dict]:
    """Process all images in a directory and export a CSV summary."""
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    images = sorted([
        f for f in image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ])

    if not images:
        logger.warning(f"No images found in {image_dir}")
        return []

    logger.info(f"Processing batch of {len(images)} images...")
    results = []

    for img_path in tqdm(images, desc="Measuring"):
        try:
            res = measure_screw(
                image_path=img_path,
                model_path=model_path,
                calibration_dir=calibration_dir,
                marker_size_mm=marker_size_mm,
                confidence_threshold=confidence_threshold
            )
            
            # Save visual output
            out_vis_path = output_dir / f"meas_{img_path.name}"
            cv2.imwrite(str(out_vis_path), res["annotated_image"])

            # Log record
            results.append({
                "image_name": img_path.name,
                "width_mm": res["width_mm"],
                "height_mm": res["height_mm"],
                "confidence": res["confidence"],
                "pixels_per_mm": res["pixels_per_mm"]
            })
            
        except Exception as e:
            logger.error(f"Failed to measure {img_path.name}: {str(e)}")

    # Export to CSV
    if results:
        df = pd.DataFrame(results)
        csv_path = output_dir / "predictions.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved metrics CSV summary to {csv_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="End-to-End Screw Metrology System.")
    parser.add_argument("--image", type=str, help="Path to single image file.")
    parser.add_argument("--image-dir", type=str, help="Directory with multiple images.")
    parser.add_argument("--model", type=str, required=True, help="Trained Mask R-CNN weights.")
    parser.add_argument("--calibration-dir", type=str, help="Camera calibration directory.")
    parser.add_argument("--marker-size", type=float, default=20.0, help="Reference marker size (mm).")
    parser.add_argument("--confidence", type=float, default=0.7, help="Prediction confidence limit.")
    parser.add_argument("--output-dir", type=str, default="measurement/results", help="Directory to save output.")

    args = parser.parse_args()

    if args.image:
        try:
            res = measure_screw(
                image_path=args.image,
                model_path=args.model,
                calibration_dir=args.calibration_dir,
                marker_size_mm=args.marker_size,
                confidence_threshold=args.confidence
            )
            
            # Output results printout
            logger.info("=" * 40)
            logger.info("Prediction Results")
            logger.info("  Object        : Phillips Screw")
            logger.info(f"  Confidence    : {res['confidence']:.2%}")
            logger.info(f"  Width (Diam)  : {res['width_mm']:.2f} mm")
            logger.info(f"  Height (Len)  : {res['height_mm']:.2f} mm")
            logger.info("=" * 40)

            # Save visual annotated image
            out_img = Path(args.output_dir) / f"meas_{Path(args.image).name}"
            out_img.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_img), res["annotated_image"])
            logger.info(f"Visual overlay saved to {out_img}")

        except Exception as e:
            logger.error(str(e))
            raise

    elif args.image_dir:
        batch_measure(
            image_dir=args.image_dir,
            model_path=args.model,
            output_dir=args.output_dir,
            calibration_dir=args.calibration_dir,
            marker_size_mm=args.marker_size,
            confidence_threshold=args.confidence
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
