# Dataset Card — Custom Screw Dataset

## 🔩 Object Selection & Rationale
We selected **Hex-Head Machine Screws** as our measurement target.
* **Dimensions:** Real-world dimensions are approximately $4.2\text{ mm}$ in diameter (width) and $22.5\text{ mm}$ in length (height).
* **Geometry:** The rigid cylinder body and hexagonal head provide crisp linear edges that are ideal for instance segmentation and oriented bounding box measurements.
* **Availability & Labelling Ease:** Screws are ubiquitous, easy to set up on a high-contrast background (e.g. white A4 paper), and the polygon boundaries between screw and background are sharp and unambiguous.

---

## 📊 Dataset Statistics & Splits

To satisfy the assessment criteria, the dataset was split into strict train, validation, and test subsets at a **70% / 20% / 10%** ratio.

| Split | Percentage | Images | Annotations | Path |
|-------|------------|--------|-------------|------|
| **Train** | 70% | 36 | 36 | [train.json](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/dataset/annotations/train.json) |
| **Validation** | 20% | 11 | 11 | [val.json](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/dataset/annotations/val.json) |
| **Test** | 10% | 4 | 4 | [test.json](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/dataset/annotations/test.json) |
| **TOTAL** | 100% | 51 | 51 | [_annotations.coco.json](file:///Users/aroonkumar/Downloads/sem_6%20Downloads/github%20session/screw-metrology-pipeline/dataset/annotations/_annotations.coco.json) |

* **Class Distribution:** 1 class (`screw` / category id `1`, supercategory `object`).
* **Format:** COCO JSON (polygon segmentation coordinates + bounding box coordinates).
* **Labeling Tool:** Exported from Roboflow in COCO JSON format.

---

## 🛠️ Collection & Labelling Strategy

### 1. Image Capture Setup
* **Camera:** iPhone main camera.
* **Resolution:** $3024 \times 4032\text{ px}$ (original).
* **Environment:** Images were captured from various angles, heights, distances, and lighting levels to ensure generalizability.
* **Scale Reference:** Each measurement image contains an **ArUco marker** ($198\text{ mm} \times 198\text{ mm}$) printed on A4 paper and positioned in the same plane as the screw.

### 2. EXIF Transposition Alignment (Critical Fix)
Smartphone portrait photos are physically saved on disk as landscape arrays (`4032 × 3024`), but contain a metadata tag to rotate them. In contrast, polygon coordinates in COCO annotations are relative to the rotated portrait view (`3024 × 4032`). 
* **The Problem:** Loading images without transposing them creates a coordinate mismatch, where bounding boxes and polygon masks are plotted in incorrect areas.
* **The Fix:** We implemented `ImageOps.exif_transpose` during dataset initialization (`models/mask_rcnn.py`), model inference (`models/inference.py`), and visualization loops. This ensures raw pixels align perfectly with the target coordinates.

---

## 🌀 Data Augmentation
Augmentation was configured inside `models/mask_rcnn.py` to prevent overfitting on the small dataset:
* **Horizontal Flip:** `RandomHorizontalFlip` (probability: 0.5)
* **Vertical Flip:** `RandomVerticalFlip` (probability: 0.5)
* **Color Jitter:** Brightness range $\pm 20\%$, contrast range $\pm 20\%$ (applied only to the image, not the mask coordinates).
* **Resize Transform:** Downscaling the image and target coordinates to fit within a $512\text{ px}$ bounding box for efficient CPU/GPU memory footprint during training.
