# Measurement Accuracy Report Template

> [!NOTE]
> This is a placeholder description file. When you run `python main.py validate`, a detailed accuracy metrics report comparing system outputs against physical calliper readings will be compiled at:
> `measurement/results/measurement_report.md`

---

## Intended Metrics to Capture

During physical measurement validation, predictions are compared against caliper ground truth values to compute accuracy:

### 1. Mean Absolute Error (MAE)
$$MAE = \frac{1}{N} \sum_{i=1}^{N} |Pred_i - GT_i|$$
- The average absolute measurement error in millimetres.

### 2. Mean Percentage Error (MPE)
$$MPE = \frac{100\%}{N} \sum_{i=1}^{N} \frac{|Pred_i - GT_i|}{GT_i}$$
- The average relative measurement error.

### Target Performance Boundaries
- **Length MPE**: < 2.0% (e.g., error < 0.4 mm for a 20 mm screw)
- **Diameter MPE**: < 5.0% (e.g., error < 0.2 mm for a 4 mm screw)
