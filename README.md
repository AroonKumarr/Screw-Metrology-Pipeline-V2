# 🔩 Screw-Metrology-Pipeline-V2

> **XIS AI Department — Technical Assessment Submission**
> An end-to-end computer vision pipeline for instance segmentation and sub-millimeter metric measurement of hex-head machine screws, powered by Mask R-CNN and intrinsic camera calibration.

---

## 🎯 Project Overview

This pipeline demonstrates a complete, production-quality **industrial metrology workflow**:

1. **Camera Calibration** — Corrects lens distortion using a checkerboard pattern so that the pixel-to-mm ratio is uniform across the entire sensor.
2. **Custom Dataset** — 51 hand-labelled screw images in COCO instance segmentation format, split 70/20/10.
3. **Mask R-CNN Segmentation** — Instance-level binary masks trained with PyTorch + TorchVision on a ResNet-50 + FPN backbone.
4. **Pixel-to-MM Metrology** — Converts segmented pixel silhouettes to real-world millimetres using an ArUco reference marker, achieving **< 0.5% measurement error**.

### Key Results (Test Set)
| Metric | Score |
|--------|-------|
| **mAP@0.5** | **1.000** |
| **mAP@0.5:0.95** | **0.775** |
| **Mean IoU** | **0.861 (86.1%)** |
| **Precision / Recall / F1** | **1.000 / 1.000 / 1.000** |
| **Width MAE** | **0.019 mm** |
| **Length MAE** | **0.067 mm** |

---

## 📁 Repository Structure

```
Screw-Metrology-Pipeline-V2/
├── calibration/
│   ├── calibrate.py           # Checkerboard corner detection + cv2.calibrateCamera
│   ├── undistort.py           # cv2.undistort wrapper for images/directories
│   ├── images/                # 25 checkerboard calibration photos
│   └── output/                # camera_matrix.npy, dist_coeffs.npy, report
├── dataset/
│   ├── train/images/          # 51 screw images (all stored here)
│   └── annotations/
│       ├── _annotations.coco.json   # Full combined COCO annotation file
│       ├── train.json               # 70% split  (36 images)
│       ├── val.json                 # 20% split  (11 images)
│       └── test.json                # 10% split  (4 images)
├── models/
│   ├── mask_rcnn.py           # ScrewDataset class + get_model() builder
│   ├── train.py               # Training loop, AdamW + CosineAnnealingLR
│   ├── evaluate.py            # mAP, IoU, Precision, Recall, F1 evaluation
│   ├── inference.py           # Single image / directory inference pipeline
│   └── weights/               # best_model.pth, training_log.json
├── measurement/
│   ├── reference_detector.py  # ArUco marker detection, pixels_per_mm
│   ├── pixel_to_mm.py         # cv2.minAreaRect → rotation-invariant conversion
│   ├── measure.py             # End-to-end: load → undistort → predict → measure
│   └── validate.py            # MAE/MPE validation against caliper ground truth
├── scripts/
│   └── split_dataset.py       # 70/20/10 reproducible COCO JSON splitter
├── notebooks/
│   └── screw_metrology_pipeline.ipynb  # Step-by-step executable walkthrough
├── docs/
│   ├── CALIBRATION_REPORT.md   # Camera matrix, distortion coefficients, error
│   ├── DATASET_CARD.md         # Object choice, splits, collection strategy
│   ├── TRAINING_REPORT.md      # Architecture, hyperparameters, metrics
│   ├── MEASUREMENT_REPORT.md   # Pixel-to-mm derivation, accuracy table
│   └── SETUP.md                # Installation, environment, troubleshooting
├── outputs/                    # Generated charts, predictions, reports
├── main.py                     # Unified CLI entry point
├── requirements.txt            # Python dependencies
└── .gitignore                  # Excludes .venv, *.pth weights, outputs
```

---

## ⚡ Quick Start

### 1. Clone and Install
```bash
git clone https://github.com/YOUR_USERNAME/Screw-Metrology-Pipeline-V2.git
cd Screw-Metrology-Pipeline-V2

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Full Pipeline via Notebook
```bash
jupyter notebook notebooks/screw_metrology_pipeline.ipynb
```
> Execute cells top-to-bottom. The notebook covers all three steps:
> - Step 1: Camera Calibration & Dataset Verification
> - Step 2: Model Training (or load existing weights) & Evaluation
> - Step 3: Pixel-to-MM Measurement & Accuracy Validation

### 3. CLI — Individual Modules
```bash
# Camera Calibration
python main.py calibrate --images calibration/images/ --output calibration/output/

# Create 70/20/10 Dataset Splits
python scripts/split_dataset.py

# Train Model
python main.py train --data-dir dataset/ --train-ann dataset/annotations/train.json \
  --val-ann dataset/annotations/val.json --epochs 15

# Evaluate on Test Set
python main.py evaluate --model models/weights/best_model.pth \
  --test-dir dataset/train/images --test-ann dataset/annotations/test.json

# Run Inference on a New Image
python main.py infer --model models/weights/best_model.pth \
  --input my_screw_image.jpg --output-dir outputs/predictions/

# Measure Real-World Dimensions
python main.py measure --image my_screw_image.jpg \
  --model models/weights/best_model.pth \
  --calibration-dir calibration/output/ \
  --marker-size 198.0
```

---

## 🔧 End-to-End Pipeline Flow

```
📷 Raw Image (EXIF Portrait, ~3024×4032)
      │
      ▼  PIL.ImageOps.exif_transpose()
📸 Correctly Oriented Image
      │
      ▼  cv2.undistort(K, D)        [uses calibration/output/*.npy]
🔧 Undistorted Image (flat pixel scale)
      │
      ├──────────────────────────────────────────┐
      ▼                                          ▼
🧠 Mask R-CNN (ResNet-50 + FPN)           🏁 ArUco DICT_4X4_50 Detector
   → Binary Instance Mask [N, H, W]          → pixels_per_mm (S)
      │                                          │
      └─────────────────┬────────────────────────┘
                        ▼
               📏 Metrology Engine
                 cv2.minAreaRect()  →  (width_px, height_px)
                 width_mm  = width_px  / S
                 height_mm = height_px / S
                        │
                        ▼
            📐 Annotated Output Image
            Width: X.XX mm | Height: Y.YY mm | Conf: ZZ%
```

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [CALIBRATION_REPORT.md](docs/CALIBRATION_REPORT.md) | Camera matrix $K$, distortion $D$, reprojection error |
| [DATASET_CARD.md](docs/DATASET_CARD.md) | Object selection, collection strategy, EXIF fix, splits |
| [TRAINING_REPORT.md](docs/TRAINING_REPORT.md) | Architecture rationale, hyperparameters, mAP/IoU/F1 |
| [MEASUREMENT_REPORT.md](docs/MEASUREMENT_REPORT.md) | Pixel-to-mm derivation, caliper vs system accuracy table |
| [SETUP.md](docs/SETUP.md) | Python environment, GPU/CPU setup, troubleshooting guide |

---

## 🏗️ Architecture: Why Mask R-CNN?

| Criterion | Mask R-CNN ✅ | U-Net ❌ | YOLOv8-Seg ❌ |
|-----------|-------------|---------|-------------|
| Instance segmentation | Per-object masks | All merged into one | Per-object masks |
| COCO pre-training | ✅ 80 classes | ImageNet only | ✅ COCO |
| Small dataset robustness | ✅ Strong | Needs more data | Needs tuning |
| Excluded by assessment | Not excluded | Not excluded | ❌ YOLO excluded |

---

## 📋 Assessment Compliance Checklist

| Requirement | Status |
|-------------|--------|
| Physical object selected & documented | ✅ Hex-head screw, ~4.2mm × 22.5mm |
| 20+ checkerboard calibration images | ✅ 25 captured, 15 successful |
| Intrinsic calibration with reprojection error | ✅ 2.084 px RMS |
| All images undistorted before use | ✅ `cv2.undistort` + EXIF transpose |
| 51 labelled images (COCO polygon format) | ✅ Roboflow export |
| 70/20/10 train/val/test split | ✅ `scripts/split_dataset.py` |
| Non-Roboflow, non-YOLO architecture | ✅ Mask R-CNN (torchvision) |
| Architecture justified | ✅ See TRAINING_REPORT.md |
| Loss curves (train/val) | ✅ `outputs/step2_loss_curves.png` |
| mAP@0.5 and mAP@0.5:0.95 logged | ✅ 1.000 / 0.775 |
| IoU, Precision, Recall, F1 logged | ✅ 0.861 / 1.0 / 1.0 / 1.0 |
| Inference on held-out test set | ✅ `outputs/step2_test_predictions.png` |
| Model card | ✅ `outputs/model_card.md` |
| ArUco pixel-to-mm conversion | ✅ `measurement/reference_detector.py` |
| Calibration dependency documented | ✅ MEASUREMENT_REPORT.md |
| Width + Height in mm output | ✅ `measurement/measure.py` |
| 10+ caliper validation measurements | ✅ MEASUREMENT_REPORT.md table |
| MAE + MPE reported | ✅ Width 0.019mm / Length 0.067mm |
| End-to-end notebook demo | ✅ `notebooks/screw_metrology_pipeline.ipynb` |
| README + all mandatory docs | ✅ `docs/` directory |
| Clean `.gitignore` | ✅ Excludes `.venv`, `*.pth`, `outputs/` |

---

*Built for the XIS AI/Computer Vision Department Technical Assessment — V2*
