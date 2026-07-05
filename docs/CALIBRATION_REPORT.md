# Camera Calibration Report

This report presents the intrinsic camera calibration parameters calculated using a checkerboard calibration target ($9 \times 6$ inner corners, $25.0\text{ mm}$ square size). These parameters are used to undistort raw images before metrology measurements are taken.

---

## 📊 Summary of Calibration Quality

| Parameter | Value | Assessment |
|-----------|-------|------------|
| **Fiducial Target** | Chessboard ($9 \times 6$ inner corners) | Standard calibration target |
| **Grid Square Size** | $25.0\text{ mm}$ | Physical side length of each checkerboard square |
| **Input Images Captured** | 25 | Total checkerboard photos taken |
| **Successful Detections** | 15 / 25 | Images used (where checkerboard was fully in-frame) |
| **Original Resolution** | $4284 \times 5712\text{ px}$ | High-resolution phone camera |
| **RMS Reprojection Error** | **2.0840 px** | Acceptable for smartphone high-resolution metrology |

> [!NOTE]
> The reprojection error represents the average distance in pixels between the corners detected in checkerboard images and the corners projected back onto the image plane using the computed calibration matrices.

---

## 📐 Calibration Parameters

### 1. Intrinsic Camera Matrix ($K$)
The intrinsic matrix maps 3D coordinates in camera space to 2D coordinates on the sensor grid:

$$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix} = \begin{bmatrix} 4104.0819 & 0.0000 & 2168.7329 \\ 0.0000 & 4097.4614 & 2751.6800 \\ 0.0000 & 0.0000 & 1.0000 \end{bmatrix}$$

* **Focal Lengths ($f_x, f_y$):** $(4104.0819, 4097.4614)\text{ px}$
* **Principal Point ($c_x, c_y$):** $(2168.7329, 2751.6800)\text{ px}$ (Optical center of the sensor)

### 2. Lens Distortion Coefficients ($D$)
Distortion coefficients compensate for the radial warping (bending of straight lines) and tangential warping (misaligned lens glass layers):

| Coefficient | Parameter Type | Computed Value | Description |
|-------------|----------------|----------------|-------------|
| **$k_1$** | Radial 1st-order | `+0.214105` | Barrel distortion (outward bending) |
| **$k_2$** | Radial 2nd-order | `-0.460082` | Correction term for higher-order radial bending |
| **$p_1$** | Tangential 1 | `-0.010775` | Horizontal tilt/decentering |
| **$p_2$** | Tangential 2 | `+0.004699` | Vertical tilt/decentering |
| **$k_3$** | Radial 3rd-order | `+0.000000` | Fixed to 0 (`CALIB_FIX_K3`) to prevent edge warping |

---

## 🔬 Distortion Correction Impact

Without correcting for lens distortion, a straight physical edge (like a screw or ruler) will appear curved near the corners of the camera view. More importantly, the **pixel-to-millimeter ratio is not uniform across a distorted sensor**, which corrupts spatial measurements.

We apply `cv2.undistort(img, K, D)` on every incoming frame. The parameters are saved locally in the calibration output folder:
* **Camera Matrix:** [camera_matrix.npy](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/calibration/output/camera_matrix.npy)
* **Distortion Coefficients:** [dist_coeffs.npy](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/calibration/output/dist_coeffs.npy)
* **Visualizations:** Found in [calibration/output/visualizations/](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/calibration/output/visualizations/)
