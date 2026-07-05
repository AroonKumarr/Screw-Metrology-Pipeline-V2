# Environment Setup Guide

## Prerequisites

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **GPU** (recommended for training): NVIDIA GPU with CUDA support
  - CUDA 11.8 or higher
  - cuDNN 8.0 or higher

---

## Step 1 — Create Virtual Environment

```bash
# Navigate to project directory
cd screw-metrology-pipeline

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

---

## Step 2 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### PyTorch with CUDA (if using GPU)

If the default PyTorch installation does not include CUDA, install manually:

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Verify Installation

```bash
python -c "
import torch
import torchvision
import cv2
import numpy as np

print(f'PyTorch:      {torch.__version__}')
print(f'TorchVision:  {torchvision.__version__}')
print(f'OpenCV:       {cv2.__version__}')
print(f'NumPy:        {np.__version__}')
print(f'CUDA:         {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU:          {torch.cuda.get_device_name(0)}')
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print('MPS (Apple):  Available')
else:
    print('Device:       CPU only')
print('All dependencies installed successfully!')
"
```

---

## Step 3 — Verify Project Structure

```bash
python -c "
from pathlib import Path
dirs = [
    'calibration/images', 'calibration/output',
    'dataset/raw', 'dataset/undistorted', 'dataset/annotations',
    'dataset/train/images', 'dataset/train/masks',
    'dataset/val/images', 'dataset/val/masks',
    'dataset/test/images', 'dataset/test/masks',
    'models/weights',
    'measurement/results',
    'outputs/predictions', 'outputs/metrics', 'outputs/reports',
]
for d in dirs:
    p = Path(d)
    status = '✓' if p.exists() else '✗ MISSING'
    print(f'  {status}  {d}')
"
```

---

## Step 4 — Hardware Recommendations

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| GPU | - | NVIDIA with 6+ GB VRAM |
| Storage | 5 GB | 20+ GB |

Training on CPU is possible but will be significantly slower (10–50× compared to GPU).

---

## Troubleshooting

### `pycocotools` installation fails on Windows

```bash
pip install pycocotools-windows
```

### OpenCV import error

```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-contrib-python
```

### CUDA out of memory during training

Reduce batch size:
```bash
python main.py train --batch-size 2
```
