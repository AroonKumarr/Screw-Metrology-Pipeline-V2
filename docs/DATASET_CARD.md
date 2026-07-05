# Dataset Card — Custom Screw Dataset

## Dataset Description
This dataset contains custom-captured, undistorted, annotated images of **Phillips Head Screws** for metrology training and evaluation.

- **Primary Object**: Phillips Head Screw (length: 19–20 mm, diameter: 3.5–4 mm)
- **Annotations**: COCO Instance Segmentation Polygons (not bounding boxes)
- **Environment**: Captured under diverse illuminations, distances, angles, and backgrounds.

---

## Dataset Splits

| Split | Percentage | Recommended Image Count | Description |
|-------|------------|-------------------------|-------------|
| **Train** | 70% | 140–210 | Used for Mask R-CNN network weight updates |
| **Validation** | 20% | 40–60 | Used for model hyperparameter optimization and loss validation |
| **Test** | 10% | 20–30 | Held-out set for final pipeline metrics calculation |

---

## Annotation Directory Structure
Annotated dataset is structured as:
```
dataset/
├── train/
│   ├── images/      # Train split RGB images
│   └── masks/       # Corresponding binary mask PNGs
├── val/
│   ├── images/      # Validation split RGB images
│   └── masks/       # Corresponding binary mask PNGs
└── test/
    ├── images/      # Test split RGB images
    └── masks/       # Corresponding binary mask PNGs
```

---

## Data Augmentation Summary
Moderate geometric and photometric augmentations applied to prevent overfitting:
- **Spatial**: Random Horizontal & Vertical Flips (probability: 0.5)
- **Photometric**: Color Jitter (brightness: 0.2, contrast: 0.2, saturation: 0.1, hue: 0.05)
- **Omitted**: Extreme scaling/affine translations to preserve geometric structural dimensions.
