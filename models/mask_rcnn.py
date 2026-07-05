"""
Mask R-CNN Model definition and Screw Dataset Class
===================================================
Defines the PyTorch Dataset for loading screw images and masks in COCO format,
and creates the Mask R-CNN network architecture using Torchvision.
"""

import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import torch
import torchvision
from torch.utils.data import Dataset
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
import numpy as np
from PIL import Image

# Import pycocotools
from pycocotools.coco import COCO


class Compose:
    """Compose data augmentations for image and target simultaneously."""
    def __init__(self, transforms: List[Callable]):
        self.transforms = transforms

    def __call__(self, image: Image.Image, target: Dict) -> Tuple[torch.Tensor, Dict]:
        for t in self.transforms:
            # Check if transform supports two arguments (e.g. geometric augmentations)
            try:
                image, target = t(image, target)
            except TypeError:
                # If only applies to image (e.g. ToTensor, ColorJitter)
                image = t(image)
        return image, target


class RandomHorizontalFlip:
    """Randomly flips the image and target masks/boxes horizontally."""
    def __init__(self, prob: float = 0.5):
        self.prob = prob

    def __call__(self, image: Image.Image, target: Dict) -> Tuple[Image.Image, Dict]:
        if torch.rand(1) < self.prob:
            # Flip image
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            
            # Update target bounding boxes
            w, h = image.size
            if "boxes" in target and target["boxes"].shape[0] > 0:
                boxes = target["boxes"]
                # boxes: [x_min, y_min, x_max, y_max]
                # flipped x_min = w - x_max
                # flipped x_max = w - x_min
                flipped_boxes = boxes.clone()
                flipped_boxes[:, [0, 2]] = w - boxes[:, [2, 0]]
                target["boxes"] = flipped_boxes
                
            # Update target masks
            if "masks" in target and target["masks"].shape[0] > 0:
                # flip masks along width dimension
                target["masks"] = torch.flip(target["masks"], dims=[2])
                
        return image, target


class RandomVerticalFlip:
    """Randomly flips the image and target masks/boxes vertically."""
    def __init__(self, prob: float = 0.5):
        self.prob = prob

    def __call__(self, image: Image.Image, target: Dict) -> Tuple[Image.Image, Dict]:
        if torch.rand(1) < self.prob:
            # Flip image
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            
            # Update target bounding boxes
            w, h = image.size
            if "boxes" in target and target["boxes"].shape[0] > 0:
                boxes = target["boxes"]
                # flipped y_min = h - y_max
                # flipped y_max = h - y_min
                flipped_boxes = boxes.clone()
                flipped_boxes[:, [1, 3]] = h - boxes[:, [3, 1]]
                target["boxes"] = flipped_boxes
                
            # Update target masks
            if "masks" in target and target["masks"].shape[0] > 0:
                # flip masks along height dimension
                target["masks"] = torch.flip(target["masks"], dims=[1])
                
        return image, target


class Resize:
    """Resize image (and scale boxes/masks) to a maximum side length."""
    def __init__(self, max_size: int = 800):
        self.max_size = max_size

    def __call__(self, image: Image.Image, target: Dict) -> Tuple[Image.Image, Dict]:
        w, h = image.size
        scale = min(self.max_size / max(w, h), 1.0)  # only downscale
        if scale == 1.0:
            return image, target
        new_w, new_h = int(w * scale), int(h * scale)
        image = image.resize((new_w, new_h), Image.BILINEAR)

        if "boxes" in target and target["boxes"].shape[0] > 0:
            target["boxes"] = target["boxes"] * scale

        if "masks" in target and target["masks"].shape[0] > 0:
            masks = target["masks"].numpy()
            resized_masks = []
            for m in masks:
                pil_m = Image.fromarray(m)
                pil_m = pil_m.resize((new_w, new_h), Image.NEAREST)
                resized_masks.append(np.array(pil_m))
            target["masks"] = torch.as_tensor(np.array(resized_masks), dtype=torch.uint8)

        return image, target


class ToTensor:
    """Convert PIL image to tensor."""
    def __call__(self, image: Image.Image) -> torch.Tensor:
        return torchvision.transforms.functional.to_tensor(image)



class ScrewDataset(Dataset):
    """
    Custom PyTorch Dataset for loading screw images and masks from COCO annotations.
    """
    def __init__(
        self,
        root_dir: Union[str, Path],
        annotation_file: Union[str, Path],
        transforms: Optional[Callable] = None,
    ):
        """
        Parameters
        ----------
        root_dir : str or Path
            Directory containing the images (e.g. dataset/train/images/).
        annotation_file : str or Path
            Path to the COCO annotations JSON.
        transforms : Callable, optional
            Data augmentations/transforms (e.g. Compose).
        """
        self.root_dir = Path(root_dir)
        self.coco = COCO(str(annotation_file))
        self.ids = list(sorted(self.coco.imgs.keys()))
        self.transforms = transforms

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, Dict]:
        coco = self.coco
        img_id = self.ids[index]
        ann_ids = coco.getAnnIds(imgIds=img_id)
        coco_annotation = coco.loadAnns(ann_ids)

        # Load image
        path = coco.loadImgs(img_id)[0]["file_name"]
        img_path = self.root_dir / path
        if not img_path.exists():
            # In case path is absolute or in nested folder
            img_path = self.root_dir / Path(path).name
            
        from PIL import ImageOps
        img = Image.open(img_path).convert("RGB")
        img = ImageOps.exif_transpose(img)
        w, h = img.size

        # Extract number of objects
        num_objs = len(coco_annotation)

        boxes = []
        masks = []
        areas = []
        iscrowd = []

        for i in range(num_objs):
            ann = coco_annotation[i]
            
            # Bounding boxes in COCO: [x_min, y_min, width, height]
            # PyTorch expects: [x_min, y_min, x_max, y_max]
            xmin, ymin, width, height = ann["bbox"]
            xmax = xmin + width
            ymax = ymin + height
            
            # Clip coordinates to image boundaries
            xmin = max(0, min(xmin, w - 1))
            ymin = max(0, min(ymin, h - 1))
            xmax = max(xmin + 1, min(xmax, w))
            ymax = max(ymin + 1, min(ymax, h))
            
            boxes.append([xmin, ymin, xmax, ymax])
            
            # Mask
            mask = coco.annToMask(ann)
            masks.append(mask)
            
            areas.append(ann.get("area", width * height))
            iscrowd.append(ann.get("iscrowd", 0))

        # Convert to PyTorch tensors
        if num_objs > 0:
            boxes = torch.as_tensor(boxes, dtype=torch.float32)
            masks = torch.as_tensor(np.array(masks), dtype=torch.uint8)
            labels = torch.ones((num_objs,), dtype=torch.int64)  # class ID for screw is 1
            image_id = torch.tensor([img_id], dtype=torch.int64)
            area = torch.as_tensor(areas, dtype=torch.float32)
            iscrowd = torch.as_tensor(iscrowd, dtype=torch.int64)
        else:
            # Handle background image (no screws)
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            masks = torch.zeros((0, h, w), dtype=torch.uint8)
            labels = torch.zeros((0,), dtype=torch.int64)
            image_id = torch.tensor([img_id], dtype=torch.int64)
            area = torch.zeros((0,), dtype=torch.float32)
            iscrowd = torch.zeros((0,), dtype=torch.int64)

        target = {
            "boxes": boxes,
            "labels": labels,
            "masks": masks,
            "image_id": image_id,
            "area": area,
            "iscrowd": iscrowd,
        }

        if self.transforms is not None:
            img, target = self.transforms(img, target)

        # Make sure image is converted to tensor if it isn't already
        if not isinstance(img, torch.Tensor):
            img = torchvision.transforms.functional.to_tensor(img)

        return img, target


def get_model(num_classes: int = 2, pretrained: bool = True) -> torchvision.models.detection.MaskRCNN:
    """
    Initialize Mask R-CNN model with a ResNet-50-FPN backbone.

    Parameters
    ----------
    num_classes : int
        Number of classes. Default 2 (background, screw).
    pretrained : bool
        If True, load pretrained weights on COCO.

    Returns
    -------
    MaskRCNN model
    """
    # Load model
    if pretrained:
        weights = torchvision.models.detection.MaskRCNN_ResNet50_FPN_Weights.DEFAULT
    else:
        weights = None
        
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(weights=weights)

    # Get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # Replace the pre-trained head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # Get number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # Replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(
        in_features_mask, hidden_layer, num_classes
    )

    return model


def get_transforms(train: bool = True) -> Compose:
    """
    Get image transformation pipeline.

    Parameters
    ----------
    train : bool
        If True, apply random training augmentations.

    Returns
    -------
    Compose pipeline
    """
    transforms_list = []

    # Always resize large images down to 512px on longest side for speed
    transforms_list.append(Resize(max_size=512))

    if train:
        # Spatial augmentations (which modify both image and ground truth masks)
        transforms_list.append(RandomHorizontalFlip(prob=0.5))
        transforms_list.append(RandomVerticalFlip(prob=0.5))
        
        # Color augmentations (which only modify the image)
        transforms_list.append(
            torchvision.transforms.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05
            )
        )

    # Convert to Tensor
    transforms_list.append(ToTensor())

    return Compose(transforms_list)
