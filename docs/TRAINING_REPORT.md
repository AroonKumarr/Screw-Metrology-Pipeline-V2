# Training Report Template

> [!NOTE]
> This is a placeholder description file. When you run `python main.py evaluate`, a detailed accuracy report based on the held-out test split will be compiled automatically at:
> `outputs/metrics/evaluation_report.md`

---

## Intended Metrics to Capture

During model evaluation, the following metrics are computed:

### 1. Precision
$$Precision = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$$
- Measures mask segmentation purity (avoiding false detections).

### 2. Recall
$$Recall = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$
- Measures model coverage (avoiding missed screws).

### 3. F1-Score
$$F_1 = 2 \times \frac{Precision \times Recall}{Precision + Recall}$$
- Harmonic mean combining Precision and Recall.

### 4. Mean Intersection over Union (mIoU)
$$IoU = \frac{\text{Area of Intersection}}{\text{Area of Union}}$$
- Evaluates polygon overlap alignment on pixel boundaries.
