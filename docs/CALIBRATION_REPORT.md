# Camera Calibration Report Template

> [!NOTE]
> This is a placeholder description file. When you run `python main.py calibrate`, a detailed report populated with your camera's actual matrices, distortion parameters, and mean reprojection error will be automatically compiled at:
> `calibration/output/calibration_report.md`

---

## Intended Metrics to Capture

During camera calibration, the following variables are estimated:

### 1. Camera Matrix (K)
$$K = \begin{bmatrix} f_x & s & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$$
- **$f_x, f_y$**: Focal lengths in pixels along width and height axes.
- **$c_x, c_y$**: Principal point coordinate (optical center in pixel space).

### 2. Lens Distortion Coefficients
Lens curvatures introduce bending of straight lines.
- **Radial distortion ($k_1, k_2, k_3$)**: Causes "barrel" or "pincushion" distortions.
- **Tangential distortion ($p_1, p_2$)**: Compensates for misalignment of lens elements to the sensor.

### 3. Reprojection Error
The Euclidean distance in pixels between corners detected in checkerboard images and corners projected back onto the image using the computed calibration matrices.
- **Target**: < 0.5 pixels
- **Optimal Range**: 0.2–0.3 pixels
