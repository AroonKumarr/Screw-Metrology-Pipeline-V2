"""
Reference Object Detector Module
================================
Detects ArUco markers in images and estimates pixels-per-mm calibration factor.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def detect_aruco_markers(
    image: np.ndarray,
    dictionary_type: int = cv2.aruco.DICT_4X4_50,
) -> Tuple[List[np.ndarray], np.ndarray, List[np.ndarray]]:
    """
    Detect ArUco markers in an image using OpenCV.
    Compatible with both OpenCV 4.7.x+ (ArucoDetector API) and older versions.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    dictionary_type : int
        OpenCV ArUco dictionary ID (default: cv2.aruco.DICT_4X4_50).

    Returns
    -------
    Tuple[List[np.ndarray], np.ndarray, List[np.ndarray]]
        - Corners of detected markers (list of 4x2 arrays)
        - IDs of detected markers (ndarray)
        - Rejected candidate corners (list)
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Retrieve dictionary object
    try:
        # OpenCV 4.7.0+ API
        aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_type)
        detector_params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, detector_params)
        corners, ids, rejected = detector.detectMarkers(gray)
    except AttributeError:
        # Pre-OpenCV 4.7.0 API
        aruco_dict = cv2.aruco.Dictionary_get(dictionary_type)
        detector_params = cv2.aruco.DetectorParameters_create()
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, aruco_dict, parameters=detector_params
        )

    # Coerce outputs to lists/arrays for uniformity
    if corners is None:
        corners = []
    if ids is None:
        ids = np.zeros((0, 1), dtype=np.int32)
    else:
        ids = np.array(ids).reshape(-1, 1)
    if rejected is None:
        rejected = []

    return list(corners), ids, list(rejected)


def get_marker_size_pixels(corners: np.ndarray) -> float:
    """
    Compute the average perimeter-based side length of a detected marker in pixels.

    Parameters
    ----------
    corners : np.ndarray
        Corners of a single ArUco marker (shape: [1, 4, 2] or [4, 2]).

    Returns
    -------
    float
        Average side length in pixels.
    """
    pts = corners.reshape(4, 2)
    
    # Calculate length of 4 sides
    side1 = np.linalg.norm(pts[0] - pts[1])
    side2 = np.linalg.norm(pts[1] - pts[2])
    side3 = np.linalg.norm(pts[2] - pts[3])
    side4 = np.linalg.norm(pts[3] - pts[0])
    
    # Return average side length
    return float((side1 + side2 + side3 + side4) / 4.0)


def compute_pixels_per_mm(
    corners: List[np.ndarray],
    known_marker_size_mm: float = 20.0,
) -> float:
    """
    Calculate the pixels-per-millimetre conversion factor from detected markers.

    Parameters
    ----------
    corners : List[np.ndarray]
        List of detected marker corners.
    known_marker_size_mm : float
        Physical width/height of the ArUco marker in millimetres (default: 20.0).

    Returns
    -------
    float
        The conversion factor (pixels/mm).
    """
    if not corners:
        raise ValueError("Cannot compute pixels-per-mm: No marker corners detected.")

    # Compute average side length across all detected markers
    pixel_sizes = [get_marker_size_pixels(c) for c in corners]
    avg_pixels = np.mean(pixel_sizes)

    pixels_per_mm = avg_pixels / known_marker_size_mm
    return float(pixels_per_mm)


def draw_markers(
    image: np.ndarray,
    corners: List[np.ndarray],
    ids: np.ndarray,
) -> np.ndarray:
    """
    Annotate image with detected ArUco markers and their IDs.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    corners : List[np.ndarray]
        Detected marker corners.
    ids : np.ndarray
        Detected marker IDs.

    Returns
    -------
    np.ndarray
        Annotated image.
    """
    vis_img = image.copy()
    if len(corners) > 0:
        cv2.aruco.drawDetectedMarkers(vis_img, corners, ids)
    return vis_img


def detect_reference(
    image: np.ndarray,
    known_marker_size_mm: float = 20.0,
    dictionary_type: int = cv2.aruco.DICT_4X4_50,
) -> Dict:
    """
    Detect ArUco marker reference and compute metric conversion factor.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    known_marker_size_mm : float
        Physical marker width/height (mm).
    dictionary_type : int
        Dictionary type.

    Returns
    -------
    Dict
        Dict of results containing 'pixels_per_mm', corners, and marker count.
    """
    corners, ids, rejected = detect_aruco_markers(image, dictionary_type)

    if len(corners) == 0:
        raise ValueError(
            "Reference object (ArUco marker) was not detected in the image. "
            "Please ensure the marker is visible and check the lighting conditions."
        )

    px_per_mm = compute_pixels_per_mm(corners, known_marker_size_mm)

    return {
        "pixels_per_mm": px_per_mm,
        "marker_corners": corners,
        "marker_ids": ids,
        "num_markers": len(corners),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Detect ArUco marker scale reference in an image.",
    )
    parser.add_argument("--image", type=str, required=True, help="Input image file.")
    parser.add_argument("--marker-size", type=float, default=20.0, help="Physical size of ArUco marker in mm.")

    args = parser.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        logger.error(f"Could not load image: {args.image}")
        return

    try:
        res = detect_reference(img, args.marker_size)
        logger.info(f"Successfully detected {res['num_markers']} marker(s)")
        logger.info(f"Conversion Factor: {res['pixels_per_mm']:.4f} pixels/mm")
        
        annotated = draw_markers(img, res["marker_corners"], res["marker_ids"])
        out_path = Path("reference_detection_output.png")
        cv2.imwrite(str(out_path), annotated)
        logger.info(f"Saved visualization to {out_path}")

    except Exception as e:
        logger.error(str(e))


if __name__ == "__main__":
    main()
