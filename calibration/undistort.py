import cv2
import numpy as np
import os
import glob
import argparse
import logging
from tqdm import tqdm
from typing import Tuple, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_calibration(calibration_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load camera calibration parameters.
    
    Args:
        calibration_dir: Directory containing camera_matrix.npy and dist_coeffs.npy.
        
    Returns:
        Tuple containing:
        - camera_matrix: 3x3 intrinsic camera matrix.
        - dist_coeffs: Distortion coefficients.
    """
    mtx_path = os.path.join(calibration_dir, 'camera_matrix.npy')
    dist_path = os.path.join(calibration_dir, 'dist_coeffs.npy')
    
    if not os.path.exists(mtx_path) or not os.path.exists(dist_path):
        raise FileNotFoundError(f"Calibration files not found in {calibration_dir}")
        
    camera_matrix = np.load(mtx_path)
    dist_coeffs = np.load(dist_path)
    
    return camera_matrix, dist_coeffs

def undistort_image(image: np.ndarray, camera_matrix: np.ndarray, dist_coeffs: np.ndarray) -> np.ndarray:
    """
    Undistort a single image array using camera calibration parameters.
    
    Args:
        image: Original image array.
        camera_matrix: 3x3 intrinsic camera matrix.
        dist_coeffs: Distortion coefficients.
        
    Returns:
        Undistorted image array.
    """
    return cv2.undistort(image, camera_matrix, dist_coeffs, None, camera_matrix)

def undistort_single(image_path: str, camera_matrix: np.ndarray, dist_coeffs: np.ndarray, output_path: Optional[str] = None) -> Optional[np.ndarray]:
    """
    Load, undistort, and optionally save a single image.
    
    Args:
        image_path: Path to the input image.
        camera_matrix: 3x3 intrinsic camera matrix.
        dist_coeffs: Distortion coefficients.
        output_path: Optional path to save the undistorted image.
        
    Returns:
        Undistorted image array, or None if loading failed.
    """
    img = cv2.imread(image_path)
    if img is None:
        logging.error(f"Failed to load image: {image_path}")
        return None
        
    undistorted = undistort_image(img, camera_matrix, dist_coeffs)
    
    if output_path is not None:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cv2.imwrite(output_path, undistorted)
        logging.info(f"Saved undistorted image to {output_path}")
        
    return undistorted

def undistort_directory(input_dir: str, output_dir: str, camera_matrix: np.ndarray, dist_coeffs: np.ndarray) -> List[str]:
    """
    Undistort all images in a directory and save them.
    
    Args:
        input_dir: Directory containing input images.
        output_dir: Directory to save undistorted images.
        camera_matrix: 3x3 intrinsic camera matrix.
        dist_coeffs: Distortion coefficients.
        
    Returns:
        List of paths to the saved undistorted images.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    exts = ['jpg', 'png', 'jpeg', 'bmp', 'JPG']
    images = []
    for ext in exts:
        images.extend(glob.glob(os.path.join(input_dir, f'*.{ext}')))
        
    if not images:
        logging.warning(f"No images found in {input_dir}")
        return []
        
    output_paths = []
    for img_path in tqdm(images, desc="Undistorting images"):
        base_name = os.path.basename(img_path)
        out_path = os.path.join(output_dir, base_name)
        
        if undistort_single(img_path, camera_matrix, dist_coeffs, out_path) is not None:
            output_paths.append(out_path)
            
    return output_paths

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Image Undistortion")
    parser.add_argument('--input', required=True, help="Path to input image or directory")
    parser.add_argument('--output', default='dataset/undistorted', help="Output path or directory")
    parser.add_argument('--calibration-dir', default='calibration/output', help="Directory containing calibration files")
    
    args = parser.parse_args()
    
    try:
        mtx, dist = load_calibration(args.calibration_dir)
        
        if os.path.isdir(args.input):
            undistort_directory(args.input, args.output, mtx, dist)
        else:
            undistort_single(args.input, mtx, dist, args.output)
            
    except Exception as e:
        logging.error(f"Error during undistortion: {e}")
