"""
Dataset Splitter — 70 / 20 / 10 Train / Val / Test
====================================================
Reads the single combined _annotations.coco.json produced by Roboflow
and writes three separate COCO-format JSON files:
  dataset/annotations/train.json   (70 % of images)
  dataset/annotations/val.json     (20 % of images)
  dataset/annotations/test.json    (10 % of images)

Usage:
    python scripts/split_dataset.py
    python scripts/split_dataset.py --seed 42 --train 0.7 --val 0.2 --test 0.1
"""

import json
import math
import random
import argparse
from pathlib import Path


def split_coco(
    src_json: Path,
    out_dir: Path,
    train_ratio: float = 0.70,
    val_ratio: float   = 0.20,
    test_ratio: float  = 0.10,
    seed: int = 42,
) -> None:
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"

    with open(src_json, encoding="utf-8") as f:
        coco = json.load(f)

    images      = coco["images"]
    annotations = coco["annotations"]
    categories  = coco["categories"]
    info        = coco.get("info", {})
    licenses    = coco.get("licenses", [])

    # Shuffle with fixed seed for reproducibility
    random.seed(seed)
    shuffled = images.copy()
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = math.ceil(n * train_ratio)
    n_val   = math.ceil(n * val_ratio)
    # test gets whatever is left
    n_test  = n - n_train - n_val

    splits = {
        "train": shuffled[:n_train],
        "val":   shuffled[n_train : n_train + n_val],
        "test":  shuffled[n_train + n_val :],
    }

    # Build annotation lookup
    id2anns: dict = {}
    for ann in annotations:
        id2anns.setdefault(ann["image_id"], []).append(ann)

    out_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split_images in splits.items():
        img_ids = {img["id"] for img in split_images}
        split_anns = [a for a in annotations if a["image_id"] in img_ids]

        coco_split = {
            "info":        info,
            "licenses":    licenses,
            "categories":  categories,
            "images":      split_images,
            "annotations": split_anns,
        }

        out_path = out_dir / f"{split_name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(coco_split, f, indent=2)

        print(f"  [{split_name:5s}]  {len(split_images):3d} images  |  "
              f"{len(split_anns):3d} annotations  →  {out_path}")

    print(f"\n✅ Split complete: {n_train} / {n_val} / {n_test}  "
          f"(train={train_ratio*100:.0f}% / val={val_ratio*100:.0f}% / test={test_ratio*100:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description="Split COCO dataset 70/20/10.")
    parser.add_argument("--src",   default="dataset/annotations/_annotations.coco.json",
                        help="Source COCO JSON file.")
    parser.add_argument("--out",   default="dataset/annotations",
                        help="Output directory for split JSONs.")
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val",   type=float, default=0.20)
    parser.add_argument("--test",  type=float, default=0.10)
    parser.add_argument("--seed",  type=int,   default=42)
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"❌ Source file not found: {src}")
        return

    print(f"📂 Source : {src}  ({src.stat().st_size // 1024} KB)")
    print(f"📁 Output : {Path(args.out)}\n")
    split_coco(src, Path(args.out), args.train, args.val, args.test, args.seed)


if __name__ == "__main__":
    main()
