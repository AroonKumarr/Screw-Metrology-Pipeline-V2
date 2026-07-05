"""
Pixel to Millimetre Conversion Module
=====================================
Calculates metrics (length, diameter/width) of a segmented object
based on contour bounding boxes and scale conversion factor.
"""

import logging
from typing import Dict, Tuple

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def mask_to_contour(mask: np.ndarray) -> np.ndarray:
    """
    Extract the largest contour from a binary mask.

    Parameters
    ----------
    mask : np.ndarray
        Binary mask (0 or 1/255, HxW).

    Returns
    -------
    np.ndarray
        The largest contour points array.
    """
    # Enforce uint8 format
    mask_u8 = mask.astype(np.uint8)
    if mask_u8.max() == 1:
        mask_u8 = mask_u8 * 255

    contours, _ = cv2.findContours(
        mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ValueError("No contours found in the provided segmentation mask.")

    # Select the largest contour by area
    largest_contour = max(contours, key=cv2.contourArea)
    return largest_contour


def get_oriented_bounding_rect(
    contour: np.ndarray
) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
    """
    Compute the minimum area rotated bounding box (minAreaRect) for a contour.

    Parameters
    ----------
    contour : np.ndarray
        Contour points.

    Returns
    -------
    Tuple
        - Center coordinates (x, y)
        - Size dimensions (width, height)
        - Rotation angle (degrees)
    """
    # rect: ((center_x, center_y), (width, height), angle)
    rect = cv2.minAreaRect(contour)
    
    center, size, angle = rect
    width, height = size

    # Align dimensions so height represents the longer side (screw length)
    # and width represents the shorter side (screw diameter/thickness)
    if width > height:
        width, height = height, width
        angle += 90.0

    return center, (width, height), angle


def measure_object_pixels(mask: np.ndarray) -> Dict:
    """
    Extract pixel width, height, center and orientation from a binary mask.

    Parameters
    ----------
    mask : np.ndarray
        Binary segmentation mask.

    Returns
    -------
    Dict
        Dictionary containing pixel-level measurement details.
    """
    contour = mask_to_contour(mask)
    center, (width_px, height_px), angle = get_oriented_bounding_rect(contour)

    return {
        "width_px": width_px,
        "height_px": height_px,
        "center": center,
        "angle": angle,
        "contour": contour,
        "rect": (center, (width_px, height_px), angle),
    }


def pixels_to_mm(pixel_value: float, pixels_per_mm: float) -> float:
    """Convert pixel measurement to physical millimetres."""
    if pixels_per_mm <= 0:
        raise ValueError("pixels_per_mm conversion factor must be positive.")
    return pixel_value / pixels_per_mm


def measure_object_mm(mask: np.ndarray, pixels_per_mm: float) -> Dict:
    """
    Extract metric (mm) dimensions from a binary mask using scale calibration.

    Parameters
    ----------
    mask : np.ndarray
        Binary mask.
    pixels_per_mm : float
        Pixels-per-mm conversion factor.

    Returns
    -------
    Dict
        Dictionary containing metric and pixel measurements.
    """
    px_measure = measure_object_pixels(mask)
    
    width_mm = pixels_to_mm(px_measure["width_px"], pixels_per_mm)
    height_mm = pixels_to_mm(px_measure["height_px"], pixels_per_mm)

    return {
        "width_mm": width_mm,
        "height_mm": height_mm,
        "width_px": px_measure["width_px"],
        "height_px": px_measure["height_px"],
        "pixels_per_mm": pixels_per_mm,
        "center": px_measure["center"],
        "angle": px_measure["angle"],
        "contour": px_measure["contour"],
        "rect": px_measure["rect"],
    }
