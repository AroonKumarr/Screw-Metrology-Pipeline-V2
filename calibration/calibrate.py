import cv2
import numpy as np
import os
import glob
import argparse
import json
import logging
from typing import Tuple, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_checkerboard_corners(image_path: str, board_size: Tuple[int, int] = (9, 6)) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Find checkerboard corners in an image.
    
    Args:
        image_path: Path to the image file.
        board_size: Tuple of (width, height) representing the number of inner corners.
        
    Returns:
        Tuple containing:
        - bool: True if corners were found successfully.
        - np.ndarray: Refined corner coordinates (or None if not found).
        - np.ndarray: The loaded image (or None if failed to load).
    """
    if not os.path.exists(image_path):
        logging.error(f"Image not found: {image_path}")
        return False, None, None

    img = cv2.imread(image_path)
    if img is None:
        logging.error(f"Failed to load image: {image_path}")
        return False, None, None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, board_size, None)
    
    if ret:
        # Refine corner locations
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        return True, corners_refined, img
    
    return False, None, img

def calibrate_camera(image_dir: str, board_size: Tuple[int, int] = (9, 6), square_size: float = 25.0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[np.ndarray], List[np.ndarray], float, Tuple[int, int]]:
    """
    Calibrate camera using a directory of checkerboard images.
    
    Args:
        image_dir: Directory containing checkerboard images.
        board_size: Tuple of (width, height) representing the number of inner corners.
        square_size: Size of a single square in mm.
        
    Returns:
        Tuple containing:
        - camera_matrix: 3x3 intrinsic camera matrix.
        - dist_coeffs: Distortion coefficients.
        - rvecs: Rotation vectors for each image.
        - tvecs: Translation vectors for each image.
        - reprojection_error: Overall RMS reprojection error.
        - image_size: Size of the images used (width, height).
    """
    logging.info(f"Starting camera calibration from {image_dir}")
    
    # Prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    objp *= square_size

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    # Supported extensions
    exts = ['jpg', 'png', 'jpeg', 'bmp', 'JPG']
    images = []
    for ext in exts:
        images.extend(glob.glob(os.path.join(image_dir, f'*.{ext}')))

    if not images:
        logging.error(f"No images found in {image_dir}")
        return None, None, [], [], 0.0, (0, 0)

    image_size = (0, 0)
    successful_images = 0

    for idx, fname in enumerate(images):
        logging.info(f"Processing image {idx + 1}/{len(images)}: {fname}")
        ret, corners, img = find_checkerboard_corners(fname, board_size)
        
        if ret and img is not None:
            objpoints.append(objp)
            imgpoints.append(corners)
            image_size = (img.shape[1], img.shape[0])
            successful_images += 1
        else:
            logging.warning(f"Could not find checkerboard in {fname}")

    logging.info(f"Successfully found corners in {successful_images}/{len(images)} images.")

    if successful_images == 0:
        logging.error("Failed to find checkerboard corners in any images.")
        return None, None, [], [], 0.0, (0, 0)

    logging.info("Calculating camera calibration parameters...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, image_size, None, None, 
        flags=cv2.CALIB_FIX_K3
    )
    
    logging.info(f"Calibration finished. Reprojection error: {ret:.4f}")
    return mtx, dist, rvecs, tvecs, ret, image_size

def save_calibration(output_dir: str, camera_matrix: np.ndarray, dist_coeffs: np.ndarray, rvecs: List[np.ndarray], tvecs: List[np.ndarray], reprojection_error: float, image_size: Tuple[int, int]) -> None:
    """
    Save calibration results to disk.
    
    Args:
        output_dir: Directory to save calibration data.
        camera_matrix: 3x3 intrinsic camera matrix.
        dist_coeffs: Distortion coefficients.
        rvecs: Rotation vectors.
        tvecs: Translation vectors.
        reprojection_error: Overall RMS reprojection error.
        image_size: Image size used for calibration (width, height).
    """
    os.makedirs(output_dir, exist_ok=True)

    np.save(os.path.join(output_dir, 'camera_matrix.npy'), camera_matrix)
    np.save(os.path.join(output_dir, 'dist_coeffs.npy'), dist_coeffs)
    
    np.savez(os.path.join(output_dir, 'calibration_data.npz'), 
             camera_matrix=camera_matrix, 
             dist_coeffs=dist_coeffs, 
             rvecs=rvecs, 
             tvecs=tvecs, 
             reprojection_error=reprojection_error,
             image_size=image_size)

    report_data = {
        'camera_matrix': camera_matrix.tolist(),
        'dist_coeffs': dist_coeffs.tolist(),
        'reprojection_error': float(reprojection_error),
        'image_size': image_size
    }
    
    with open(os.path.join(output_dir, 'calibration_report.json'), 'w') as f:
        json.dump(report_data, f, indent=4)
        
    logging.info(f"Calibration data saved to {output_dir}")

def generate_calibration_report(output_dir: str, camera_matrix: np.ndarray, dist_coeffs: np.ndarray, reprojection_error: float, num_images: int, image_size: Tuple[int, int]) -> None:
    """
    Generate a human-readable markdown report of the calibration.
    """
    quality = "Poor"
    if reprojection_error < 0.3:
        quality = "Excellent"
    elif reprojection_error < 0.5:
        quality = "Good"
    elif reprojection_error < 1.0:
        quality = "Acceptable"

    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]

    report = f"""# Camera Calibration Report

## Overall Quality Assessment
- **Quality**: {quality}
- **Reprojection Error**: {reprojection_error:.4f} pixels
- **Images Used**: {num_images}
- **Image Size**: {image_size[0]}x{image_size[1]}

## Camera Matrix (Intrinsics)
```
[{camera_matrix[0, 0]:.4f}, {camera_matrix[0, 1]:.4f}, {camera_matrix[0, 2]:.4f}]
[{camera_matrix[1, 0]:.4f}, {camera_matrix[1, 1]:.4f}, {camera_matrix[1, 2]:.4f}]
[{camera_matrix[2, 0]:.4f}, {camera_matrix[2, 1]:.4f}, {camera_matrix[2, 2]:.4f}]
```
- Focal Length (fx, fy): ({fx:.4f}, {fy:.4f})
- Principal Point (cx, cy): ({cx:.4f}, {cy:.4f})

## Distortion Coefficients
`k1, k2, p1, p2, k3`
```
[{dist_coeffs[0, 0]:.6f}, {dist_coeffs[0, 1]:.6f}, {dist_coeffs[0, 2]:.6f}, {dist_coeffs[0, 3]:.6f}, {dist_coeffs[0, 4]:.6f}]
```
"""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, 'calibration_report.md')
    with open(report_path, 'w') as f:
        f.write(report)
        
    logging.info(f"Calibration report saved to {report_path}")

def visualize_calibration(image_dir: str, output_dir: str, camera_matrix: np.ndarray, dist_coeffs: np.ndarray, board_size: Tuple[int, int] = (9, 6)) -> None:
    """
    Draw detected corners and save side-by-side original vs undistorted comparisons.
    """
    vis_dir = os.path.join(output_dir, 'visualizations')
    os.makedirs(vis_dir, exist_ok=True)
    
    exts = ['jpg', 'png', 'jpeg', 'bmp', 'JPG']
    images = []
    for ext in exts:
        images.extend(glob.glob(os.path.join(image_dir, f'*.{ext}')))

    for idx, fname in enumerate(images):
        ret, corners, img = find_checkerboard_corners(fname, board_size)
        if ret and img is not None:
            # Draw corners
            img_with_corners = img.copy()
            cv2.drawChessboardCorners(img_with_corners, board_size, corners, ret)
            
            # Undistort
            undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, camera_matrix)
            
            # Combine side by side
            h, w = img.shape[:2]
            combined = np.zeros((h, w * 2, 3), dtype=np.uint8)
            combined[:, :w] = img_with_corners
            combined[:, w:] = undistorted
            
            # Save
            base_name = os.path.basename(fname)
            vis_path = os.path.join(vis_dir, f"vis_{base_name}")
            cv2.imwrite(vis_path, combined)
            
    logging.info(f"Visualizations saved to {vis_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Camera Calibration")
    parser.add_argument('--images', required=True, help="Path to checkerboard images")
    parser.add_argument('--output', default='calibration/output', help="Output directory")
    parser.add_argument('--board-size', default='9,6', help="Checkerboard size (e.g., 9,6)")
    parser.add_argument('--square-size', type=float, default=25.0, help="Square size in mm")
    
    args = parser.parse_args()
    
    try:
        w, h = map(int, args.board_size.split(','))
        board_size = (w, h)
    except ValueError:
        logging.error("Invalid board size format. Use width,height (e.g., 9,6)")
        exit(1)
    
    mtx, dist, rvecs, tvecs, err, img_size = calibrate_camera(args.images, board_size, args.square_size)
    
    if mtx is not None:
        save_calibration(args.output, mtx, dist, rvecs, tvecs, err, img_size)
        generate_calibration_report(args.output, mtx, dist, err, len(rvecs), img_size)
        visualize_calibration(args.images, args.output, mtx, dist, board_size)
