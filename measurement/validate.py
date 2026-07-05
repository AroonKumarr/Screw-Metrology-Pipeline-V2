"""
Accuracy Validation Module
==========================
Compares predicted measurements against physical calliper readings.
Computes Mean Absolute Error (MAE) and Mean Percentage Error (MPE).
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_ground_truth(csv_path: str) -> pd.DataFrame:
    """Load Ground Truth Caliper measurements from a CSV file."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Ground truth CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    required_cols = {"image_name", "width_mm", "height_mm"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Ground truth CSV must contain columns: {required_cols}")

    return df


def compute_errors(
    predictions_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
) -> Tuple[Dict, pd.DataFrame]:
    """
    Match predictions to ground truth by image name and compute errors.
    """
    # Merge on image name
    merged = pd.merge(
        predictions_df,
        ground_truth_df,
        on="image_name",
        suffixes=("_pred", "_gt")
    )

    if merged.empty:
        raise ValueError("Could not match any predictions with ground truth. Check image names.")

    # Width Error (diameter)
    merged["abs_error_width"] = (merged["width_mm_pred"] - merged["width_mm_gt"]).abs()
    merged["pct_error_width"] = (merged["abs_error_width"] / merged["width_mm_gt"]) * 100.0

    # Height Error (length)
    merged["abs_error_height"] = (merged["height_mm_pred"] - merged["height_mm_gt"]).abs()
    merged["pct_error_height"] = (merged["abs_error_height"] / merged["height_mm_gt"]) * 100.0

    # Aggregate Statistics
    metrics = {
        "num_samples": len(merged),
        "width": {
            "mae": float(merged["abs_error_width"].mean()),
            "mpe": float(merged["pct_error_width"].mean()),
            "rmse": float(np.sqrt((merged["abs_error_width"] ** 2).mean())),
            "max_error": float(merged["abs_error_width"].max()),
        },
        "height": {
            "mae": float(merged["abs_error_height"].mean()),
            "mpe": float(merged["pct_error_height"].mean()),
            "rmse": float(np.sqrt((merged["abs_error_height"] ** 2).mean())),
            "max_error": float(merged["abs_error_height"].max()),
        }
    }

    return metrics, merged


def generate_validation_plots(
    df: pd.DataFrame,
    output_dir: Path
) -> None:
    """Generate plots showing errors and correlations."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Height correlation plot
    plt.figure(figsize=(6, 6))
    max_val = max(df["height_mm_gt"].max(), df["height_mm_pred"].max()) + 2
    min_val = min(df["height_mm_gt"].min(), df["height_mm_pred"].min()) - 2
    plt.scatter(df["height_mm_gt"], df["height_mm_pred"], color="blue", label="Screws")
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label="Perfect Match (1:1)")
    plt.xlabel("Ground Truth (Caliper mm)")
    plt.ylabel("System Prediction (mm)")
    plt.title("Screw Length (Height) Prediction vs Ground Truth")
    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "length_correlation.png")
    plt.close()

    # 2. Width correlation plot
    plt.figure(figsize=(6, 6))
    max_val = max(df["width_mm_gt"].max(), df["width_mm_pred"].max()) + 1
    min_val = min(df["width_mm_gt"].min(), df["width_mm_pred"].min()) - 1
    plt.scatter(df["width_mm_gt"], df["width_mm_pred"], color="green", label="Screws")
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label="Perfect Match (1:1)")
    plt.xlabel("Ground Truth (Caliper mm)")
    plt.ylabel("System Prediction (mm)")
    plt.title("Screw Diameter (Width) Prediction vs Ground Truth")
    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "diameter_correlation.png")
    plt.close()

    # 3. Bar chart of errors per sample
    plt.figure(figsize=(10, 5))
    x = np.arange(len(df))
    w = 0.35
    plt.bar(x - w/2, df["abs_error_height"], w, label="Length Abs Error (mm)", color="skyblue")
    plt.bar(x + w/2, df["abs_error_width"], w, label="Diameter Abs Error (mm)", color="lightcoral")
    plt.xticks(x, df["image_name"], rotation=45, ha="right")
    plt.ylabel("Absolute Error (mm)")
    plt.title("Absolute Measurement Errors per Image")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "error_per_sample.png")
    plt.close()


def generate_validation_report(
    metrics: Dict,
    df: pd.DataFrame,
    output_dir: Path
) -> None:
    """Create Markdown accuracy report."""
    
    # Generate error table
    rows = []
    for _, r in df.iterrows():
        rows.append(
            f"| {r['image_name']} | "
            f"{r['height_mm_gt']:.2f} | {r['height_mm_pred']:.2f} | {r['abs_error_height']:.2f} ({r['pct_error_height']:.2f}%) | "
            f"{r['width_mm_gt']:.2f} | {r['width_mm_pred']:.2f} | {r['abs_error_width']:.2f} ({r['pct_error_width']:.2f}%) |"
        )
    table_content = "\n".join(rows)

    md_content = f"""# Measurement Validation Report

## Metric Performance Summary
Caliper comparisons computed across {metrics['num_samples']} matched screw instances.

| Dimension | Mean Absolute Error (MAE) | Mean Percentage Error (MPE) | Root Mean Squared Error (RMSE) | Max Error |
|-----------|---------------------------|------------------------------|--------------------------------|-----------|
| **Length (Height)** | {metrics['height']['mae']:.3f} mm | {metrics['height']['mpe']:.2f}% | {metrics['height']['rmse']:.3f} mm | {metrics['height']['max_error']:.3f} mm |
| **Diameter (Width)** | {metrics['width']['mae']:.3f} mm | {metrics['width']['mpe']:.2f}% | {metrics['width']['rmse']:.3f} mm | {metrics['width']['max_error']:.3f} mm |

## Per-Sample Error Details
Below is the breakdown of validation error for each target screw.

| Image Name | GT Length (mm) | Pred Length (mm) | Length Error (MPE) | GT Diam (mm) | Pred Diam (mm) | Diam Error (MPE) |
|------------|----------------|------------------|-------------------|--------------|----------------|------------------|
{table_content}

## Accuracy Assessment
- **Length Target (MPE < 2.0%)**: {"Pass" if metrics['height']['mpe'] < 2.0 else "Fail"}
- **Diameter Target (MPE < 5.0%)**: {"Pass" if metrics['width']['mpe'] < 5.0 else "Fail"}

---
*Report generated automatically by Accuracy Validation Module.*
"""

    with open(output_dir / "measurement_report.md", "w") as f:
        f.write(md_content)
    logger.info(f"Markdown validation report saved: {output_dir / 'measurement_report.md'}")


def validate(
    predictions_csv: str,
    ground_truth_csv: str,
    output_dir: str
) -> Dict:
    """Run validation workflow."""
    pred_df = pd.read_csv(predictions_csv)
    gt_df = load_ground_truth(ground_truth_csv)

    metrics, merged = compute_errors(pred_df, gt_df)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save outputs
    generate_validation_plots(merged, output_dir)
    generate_validation_report(metrics, merged, output_dir)
    
    # Save statistics JSON
    with open(output_dir / "validation_stats.json", "w") as f:
        json.dump(metrics, f, indent=4)

    logger.info("Validation workflow completed successfully.")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Validate Metrology System Accuracy.")
    parser.add_argument("--predictions", type=str, required=True, help="Predictions summary CSV.")
    parser.add_argument("--ground-truth", type=str, required=True, help="Ground truth caliper CSV.")
    parser.add_argument("--output-dir", type=str, default="measurement/results", help="Directory to save plots/report.")

    args = parser.parse_args()

    validate(args.predictions, args.ground_truth, args.output_dir)


if __name__ == "__main__":
    main()
