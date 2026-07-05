# Screw Metrology Pipeline

## End-to-End Computer Vision Pipeline for Screw Segmentation and Real-World Metric Measurement

This project implements a complete computer vision system that:

1. **Calibrates a camera** to remove lens distortion
2. **Segments screws** using a Mask R-CNN instance segmentation model
3. **Measures screw dimensions** in millimetres using ArUco markers as reference objects

---

## Project Architecture

```
Input Image
     │
     ▼
Camera Calibration (Camera Matrix + Distortion Coefficients)
     │
     ▼
Image Undistortion (cv2.undistort)
     │
     ▼
Mask R-CNN Inference (Instance Segmentation)
     │
     ▼
Reference Object Detection (ArUco Marker)
     │
     ▼
Pixel-to-Millimetre Conversion
     │
     ▼
Width + Height + Confidence + Visualization
```

---

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Camera Calibration

```bash
# Place 20-30 checkerboard images in calibration/images/
python main.py calibrate --images calibration/images/ --board-size 9,6 --square-size 25.0
```

### 3. Prepare Dataset

```bash
# Place raw screw images in dataset/raw/
python main.py prepare --raw-dir dataset/raw/ --calibration-dir calibration/output/
```

### 4. Train Model

```bash
# After annotating images with COCO-format labels
python main.py train --data-dir dataset/ --epochs 100 --batch-size 4
```

### 5. Measure Screws

```bash
# Run measurement on a new image
python main.py measure --image path/to/image.jpg --model models/weights/best_model.pth
```

### 6. Validate Accuracy

```bash
# Compare predictions against caliper measurements
python main.py validate --predictions measurement/results/predictions.csv --ground-truth measurement/ground_truth.csv
```

---

## Repository Structure

```
screw-metrology-pipeline/
│
├── calibration/               # Camera calibration module
│   ├── images/                # Checkerboard calibration images
│   ├── output/                # Calibration results (camera_matrix.npy, etc.)
│   ├── calibrate.py           # Calibration script
│   ├── undistort.py           # Image undistortion script
│   └── __init__.py
│
├── dataset/                   # Dataset management
│   ├── raw/                   # Raw screw images (user-provided)
│   ├── undistorted/           # Undistorted images (auto-generated)
│   ├── annotations/           # COCO-format annotations (user-provided)
│   ├── train/                 # Training split
│   │   ├── images/
│   │   └── masks/
│   ├── val/                   # Validation split
│   │   ├── images/
│   │   └── masks/
│   ├── test/                  # Test split
│   │   ├── images/
│   │   └── masks/
│   ├── prepare_dataset.py     # Dataset preparation script
│   └── __init__.py
│
├── models/                    # Deep learning module
│   ├── weights/               # Trained model weights
│   ├── mask_rcnn.py           # Model definition + dataset class
│   ├── train.py               # Training script
│   ├── evaluate.py            # Evaluation metrics
│   ├── inference.py           # Inference pipeline
│   └── __init__.py
│
├── measurement/               # Measurement module
│   ├── results/               # Measurement outputs
│   ├── reference_detector.py  # ArUco marker detection
│   ├── pixel_to_mm.py         # Pixel-to-mm conversion
│   ├── measure.py             # Full measurement pipeline
│   ├── validate.py            # Accuracy validation
│   └── __init__.py
│
├── docs/                      # Documentation
│   ├── SETUP.md
│   ├── CALIBRATION_REPORT.md
│   ├── DATASET_CARD.md
│   ├── TRAINING_REPORT.md
│   └── MEASUREMENT_REPORT.md
│
├── outputs/                   # Pipeline outputs
│   ├── predictions/
│   ├── metrics/
│   └── reports/
│
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Detailed Usage

### Camera Calibration

Print a checkerboard pattern (e.g., 9×6 inner corners) and capture 20–30 images from various angles, distances, and rotations.

```bash
python main.py calibrate \
    --images calibration/images/ \
    --output calibration/output/ \
    --board-size 9,6 \
    --square-size 25.0
```

**Target reprojection error:** < 0.5 pixels (ideally 0.2–0.3 pixels)

### Dataset Annotation

Use a polygon-based annotation tool:
- **[CVAT](https://cvat.ai/)** (recommended)
- **[LabelMe](https://github.com/labelmeai/labelme)**
- **[Roboflow](https://roboflow.com/)** (annotation only)

Export annotations in **COCO JSON format**.

### Model Training

```bash
python main.py train \
    --data-dir dataset/ \
    --train-ann dataset/annotations/train_annotations.json \
    --val-ann dataset/annotations/val_annotations.json \
    --epochs 100 \
    --batch-size 4 \
    --lr 0.0001 \
    --output-dir models/weights/
```

### Measurement

Place an **ArUco marker** (known size) in the image alongside the screw.

```bash
python main.py measure \
    --image path/to/screw_with_marker.jpg \
    --model models/weights/best_model.pth \
    --calibration-dir calibration/output/ \
    --marker-size 20.0 \
    --output-dir measurement/results/
```

**Output:**
```
========================================
  Prediction Results
  Object        : Screw
  Confidence    : 99.1%
  Width         : 3.87 mm
  Height        : 19.14 mm
========================================
```

---

## Model Architecture

**Mask R-CNN** with ResNet-50-FPN backbone:
- Pre-trained on COCO dataset
- Fine-tuned on custom screw dataset
- Produces instance segmentation masks + bounding boxes + confidence scores

**Why Mask R-CNN?**
- Designed for instance segmentation
- Well-researched and academically accepted
- Works well on small datasets with transfer learning
- Not a YOLO or Roboflow-hosted model (as per project requirements)

---

## Measurement Method

1. **ArUco marker detection** provides a known physical reference
2. **Pixels-per-mm ratio** computed from marker dimensions
3. **Minimum area rotated rectangle** around the screw mask gives orientation-invariant width/height
4. **Pixel dimensions × conversion ratio** = millimetre measurements

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| mAP@0.5 | Mean Average Precision at IoU=0.5 |
| mAP@0.5:0.95 | Mean Average Precision across IoU thresholds |
| IoU | Intersection over Union |
| Precision | True Positives / (TP + FP) |
| Recall | True Positives / (TP + FN) |
| F1-Score | Harmonic mean of Precision and Recall |
| MAE | Mean Absolute Error (mm) |
| MPE | Mean Percentage Error (%) |

---

## Requirements

- Python 3.9+
- PyTorch 2.0+
- OpenCV 4.8+
- CUDA-capable GPU (recommended for training)

See [requirements.txt](requirements.txt) for complete dependency list.

---

## License

This project is developed for academic assessment purposes.
