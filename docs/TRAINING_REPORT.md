# Model Training and Evaluation Report

This report documents the architecture selection, training parameters, and performance metrics of the segmentation model evaluated on the held-out test split (10% of the dataset).

---

## 🧠 Model Selection & Justification

We selected **Mask R-CNN (ResNet-50 + FPN)** for instance segmentation:
* **Alternative (U-Net/DeepLab):** These architectures perform semantic segmentation, grouping all screws into a single mask layer. If two screws lay close together, semantic networks merge them into one blob, making individual measurements impossible.
* **Alternative (YOLOv8-Seg):** While extremely fast, YOLO training is optimized for large datasets and is less robust to precise boundary classification under very small datasets (e.g. 51 images) without extensive hyperparameter grid search.
* **Mask R-CNN Choice:** It treats each screw as an independent object instance, outputting both a refined bounding box and a high-resolution pixel-level binary mask. Its ResNet-50 backbone with Feature Pyramid Network (FPN) extracts multi-scale details to resolve screw thread boundaries, and COCO pretraining enables robust fine-tuning with only 51 custom images.

---

## ⚙️ Hyperparameters and Training Setup

The training script (`models/train.py`) was run with the following settings:
* **Framework:** PyTorch + TorchVision
* **Pretrained Weights:** COCO Mask R-CNN ResNet-50 FPN
* **Device:** CPU (selected for memory stability and deadlock prevention)
* **Epochs:** 15 (optimized for rapid training cycles)
* **Batch Size:** 1
* **Base Learning Rate:** $1\times10^{-4}$
* **Optimizer:** `AdamW` (weight decay: $5\times10^{-4}$)
* **Learning Rate Scheduler:** `CosineAnnealingLR` (cosing decay to 0 over 15 epochs)
* **Resizing:** Images and target coordinates resized to a maximum side length of $512\text{ px}$ for feature extraction.

---

## 📊 Held-Out Test Set Performance

The model was evaluated against the **10% held-out test set** (unseen during training) at multiple Intersection over Union (IoU) thresholds:

| Metric | Target Value | Model Score | Evaluation |
|--------|--------------|-------------|------------|
| **Precision** | $> 0.85$ | **1.0000** | ✅ Pass |
| **Recall** | $> 0.85$ | **1.0000** | ✅ Pass |
| **F1-Score** | $> 0.85$ | **1.0000** | ✅ Pass |
| **Mean IoU** | $> 0.70$ | **0.8611 (86.11%)** | ✅ Pass |
| **mAP@0.5** | — | **1.0000** | ✅ Pass |
| **mAP@0.5:0.95** | — | **0.7750** | ✅ Pass |

### 📈 Training Loss & Validation Metrics
* **Initial Training Loss:** `0.6578` (Epoch 1)
* **Final Training Loss:** `0.1415` (Epoch 15)
* **Best Validation Loss:** `0.1420` (Epoch 15)
* **Loss Curves Plot:** Saved in the project directory at [loss_curves.png](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/models/weights/loss_curves.png).
* **Metrics Visualization:** Interactive charts and predictions on the test set are saved in [outputs/metrics/](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/outputs/metrics/) and visual plots in [outputs/](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/outputs/).
