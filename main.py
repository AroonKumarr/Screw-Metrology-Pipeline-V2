#!/usr/bin/env python
"""
Screw Metrology Pipeline — Entry Point CLI
==========================================
Unified interface for running calibration, dataset preparation,
training, evaluation, metrology measurement, and accuracy validation.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import CLI modules
import calibration.calibrate as calibrate_mod
import calibration.undistort as undistort_mod
import dataset.prepare_dataset as dataset_mod
import models.train as train_mod
import models.evaluate as evaluate_mod
import models.inference as inference_mod
import measurement.measure as measure_mod
import measurement.validate as validate_mod


def parse_args():
    parser = argparse.ArgumentParser(
        description="End-to-End Metrology System for Screw Segmentation and Measurement.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Pipeline phase command.")

    # ──────────────────────────────────────────────────────────
    # CALIBRATE
    # ──────────────────────────────────────────────────────────
    parser_cal = subparsers.add_parser("calibrate", help="Run Camera Calibration.")
    parser_cal.add_argument(
        "--images", type=str, required=True,
        help="Directory containing checkerboard calibration images."
    )
    parser_cal.add_argument(
        "--output", type=str, default="calibration/output",
        help="Output directory to save parameters (default: calibration/output)."
    )
    parser_cal.add_argument(
        "--board-size", type=str, default="9,6",
        help="Grid dimensions specified as cols,rows (default: 9,6)."
    )
    parser_cal.add_argument(
        "--square-size", type=float, default=25.0,
        help="Physical length of each checkerboard square in mm (default: 25.0)."
    )

    # ──────────────────────────────────────────────────────────
    # UNDISTORT
    # ──────────────────────────────────────────────────────────
    parser_und = subparsers.add_parser("undistort", help="Undistort images using parameters.")
    parser_und.add_argument(
        "--input", type=str, required=True,
        help="Single image file or folder containing distorted images."
    )
    parser_und.add_argument(
        "--output", type=str, default="dataset/undistorted",
        help="Save directory or file path for undistorted images."
    )
    parser_und.add_argument(
        "--calibration-dir", type=str, default="calibration/output",
        help="Path containing camera parameters (default: calibration/output)."
    )

    # ──────────────────────────────────────────────────────────
    # PREPARE DATASET
    # ──────────────────────────────────────────────────────────
    parser_prep = subparsers.add_parser("prepare", help="Prepare train/val/test splits.")
    parser_prep.add_argument(
        "--raw-dir", type=str, required=True,
        help="Directory containing raw screw dataset images."
    )
    parser_prep.add_argument(
        "--output-dir", type=str, default="dataset",
        help="Dataset directory to export splits (default: dataset)."
    )
    parser_prep.add_argument(
        "--annotation-file", type=str, default=None,
        help="Master COCO JSON file (optional)."
    )
    parser_prep.add_argument(
        "--calibration-dir", type=str, default=None,
        help="Camera parameters directory to undistort images (optional)."
    )
    parser_prep.add_argument(
        "--train-ratio", type=float, default=0.7, help="Train ratio (default: 0.7)."
    )
    parser_prep.add_argument(
        "--val-ratio", type=float, default=0.2, help="Val ratio (default: 0.2)."
    )
    parser_prep.add_argument(
        "--test-ratio", type=float, default=0.1, help="Test ratio (default: 0.1)."
    )

    # ──────────────────────────────────────────────────────────
    # TRAIN
    # ──────────────────────────────────────────────────────────
    parser_train = subparsers.add_parser("train", help="Train Mask R-CNN model.")
    parser_train.add_argument(
        "--data-dir", type=str, default="dataset",
        help="Dataset root directory containing train/val folders."
    )
    parser_train.add_argument(
        "--train-ann", type=str, required=True,
        help="Path to training COCO annotations JSON."
    )
    parser_train.add_argument(
        "--val-ann", type=str, required=True,
        help="Path to validation COCO annotations JSON."
    )
    parser_train.add_argument(
        "--epochs", type=int, default=80, help="Epoch limit (default: 80)."
    )
    parser_train.add_argument(
        "--batch-size", type=int, default=4, help="Batch size."
    )
    parser_train.add_argument(
        "--lr", type=float, default=0.0001, help="Learning rate."
    )
    parser_train.add_argument(
        "--output-dir", type=str, default="models/weights",
        help="Weights save directory (default: models/weights)."
    )

    # ──────────────────────────────────────────────────────────
    # EVALUATE
    # ──────────────────────────────────────────────────────────
    parser_eval = subparsers.add_parser("evaluate", help="Evaluate model accuracy.")
    parser_eval.add_argument(
        "--model", type=str, required=True,
        help="Path to trained weights .pth file."
    )
    parser_eval.add_argument(
        "--test-dir", type=str, required=True,
        help="Directory containing the test images."
    )
    parser_eval.add_argument(
        "--test-ann", type=str, required=True,
        help="Test COCO annotation JSON."
    )
    parser_eval.add_argument(
        "--output-dir", type=str, default="outputs/metrics",
        help="Metrics output folder."
    )

    # ──────────────────────────────────────────────────────────
    # INFERENCE
    # ──────────────────────────────────────────────────────────
    parser_inf = subparsers.add_parser("predict", help="Predict segmentation masks.")
    parser_inf.add_argument(
        "--model", type=str, required=True, help="Trained model path."
    )
    parser_inf.add_argument(
        "--input", type=str, required=True, help="Input image file or folder."
    )
    parser_inf.add_argument(
        "--output-dir", type=str, default="outputs/predictions",
        help="Visualization save directory."
    )
    parser_inf.add_argument(
        "--confidence", type=float, default=0.5, help="Confidence boundary."
    )

    # ──────────────────────────────────────────────────────────
    # MEASURE
    # ──────────────────────────────────────────────────────────
    parser_meas = subparsers.add_parser("measure", help="Measure screw size from image.")
    parser_meas.add_argument(
        "--image", type=str, help="Single image file."
    )
    parser_meas.add_argument(
        "--image-dir", type=str, help="Directory containing images."
    )
    parser_meas.add_argument(
        "--model", type=str, required=True, help="Trained weights path."
    )
    parser_meas.add_argument(
        "--calibration-dir", type=str, help="Camera parameters path."
    )
    parser_meas.add_argument(
        "--marker-size", type=float, default=20.0,
        help="Physical reference marker size in mm (default: 20.0)."
    )
    parser_meas.add_argument(
        "--confidence", type=float, default=0.7, help="Prediction threshold."
    )
    parser_meas.add_argument(
        "--output-dir", type=str, default="measurement/results",
        help="Output results directory (default: measurement/results)."
    )

    # ──────────────────────────────────────────────────────────
    # VALIDATE ACCURACY
    # ──────────────────────────────────────────────────────────
    parser_val = subparsers.add_parser("validate", help="Validate prediction accuracy.")
    parser_val.add_argument(
        "--predictions", type=str, required=True,
        help="Predictions CSV from batch-measure output."
    )
    parser_val.add_argument(
        "--ground-truth", type=str, required=True,
        help="Caliper ground truth measurements CSV."
    )
    parser_val.add_argument(
        "--output-dir", type=str, default="measurement/results",
        help="Validation report save directory."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "calibrate":
        board_size_tup = tuple(map(int, args.board_size.split(",")))
        res = calibrate_mod.calibrate_camera(
            image_dir=args.images,
            board_size=board_size_tup,
            square_size=args.square_size
        )
        camera_matrix, dist_coeffs, rvecs, tvecs, err, size = res
        calibrate_mod.save_calibration(args.output, camera_matrix, dist_coeffs, rvecs, tvecs, err, size)
        calibrate_mod.generate_calibration_report(args.output, camera_matrix, dist_coeffs, err, size)
        calibrate_mod.visualize_calibration(args.images, args.output, camera_matrix, dist_coeffs, board_size_tup)

    elif args.command == "undistort":
        camera_matrix, dist_coeffs = undistort_mod.load_calibration(args.calibration_dir)
        input_path = Path(args.input)
        if input_path.is_dir():
            undistort_mod.undistort_directory(input_path, args.output, camera_matrix, dist_coeffs)
        else:
            out_path = Path(args.output)
            if out_path.suffix == "":
                out_path = out_path / input_path.name
            undistort_mod.undistort_single(input_path, camera_matrix, dist_coeffs, out_path)

    elif args.command == "prepare":
        dataset_mod.prepare_full_dataset(
            raw_dir=args.raw_dir,
            output_dir=args.output_dir,
            annotation_file=args.annotation_file,
            calibration_dir=args.calibration_dir,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio
        )

    elif args.command == "train":
        train_mod.train_model(vars(args))

    elif args.command == "evaluate":
        evaluate_mod.evaluate_model(
            model_path=args.model,
            test_dir=args.test_dir,
            annotation_file=args.test_ann,
            output_dir=args.output_dir
        )

    elif args.command == "predict":
        inference_mod.run_inference(
            model_path=args.model,
            input_path=args.input,
            output_dir=args.output_dir,
            confidence_threshold=args.confidence
        )

    elif args.command == "measure":
        if args.image:
            res = measure_mod.measure_screw(
                image_path=args.image,
                model_path=args.model,
                calibration_dir=args.calibration_dir,
                marker_size_mm=args.marker_size,
                confidence_threshold=args.confidence
            )
            print("=" * 40)
            print("Metrology Measurement Results")
            print("  Object      : Phillips Screw")
            print(f"  Confidence  : {res['confidence']:.2%}")
            print(f"  Length      : {res['height_mm']:.2f} mm")
            print(f"  Diameter    : {res['width_mm']:.2f} mm")
            print("=" * 40)
            
            # Save visual
            out_img = Path(args.output_dir) / f"meas_{Path(args.image).name}"
            out_img.parent.mkdir(parents=True, exist_ok=True)
            import cv2
            cv2.imwrite(str(out_img), res["annotated_image"])
            print(f"Annotated result saved: {out_img}")
            
        elif args.image_dir:
            measure_mod.batch_measure(
                image_dir=args.image_dir,
                model_path=args.model,
                output_dir=args.output_dir,
                calibration_dir=args.calibration_dir,
                marker_size_mm=args.marker_size,
                confidence_threshold=args.confidence
            )
        else:
            print("Error: Specify either --image or --image-dir for measurement phase.")
            sys.exit(1)

    elif args.command == "validate":
        validate_mod.validate(args.predictions, args.ground_truth, args.output_dir)


if __name__ == "__main__":
    main()
