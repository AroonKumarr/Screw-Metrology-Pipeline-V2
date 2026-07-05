"""Measurement and Metrology validation module."""

from measurement.reference_detector import (
    detect_aruco_markers,
    get_marker_size_pixels,
    compute_pixels_per_mm,
    draw_markers,
    detect_reference,
)
from measurement.pixel_to_mm import (
    mask_to_contour,
    get_oriented_bounding_rect,
    measure_object_pixels,
    pixels_to_mm,
    measure_object_mm,
)
from measurement.measure import (
    measure_screw,
    visualize_measurement,
    batch_measure,
)
from measurement.validate import (
    load_ground_truth,
    compute_errors,
    generate_validation_plots,
    generate_validation_report,
    validate,
)

__all__ = [
    "detect_aruco_markers",
    "get_marker_size_pixels",
    "compute_pixels_per_mm",
    "draw_markers",
    "detect_reference",
    "mask_to_contour",
    "get_oriented_bounding_rect",
    "measure_object_pixels",
    "pixels_to_mm",
    "measure_object_mm",
    "measure_screw",
    "visualize_measurement",
    "batch_measure",
    "load_ground_truth",
    "compute_errors",
    "generate_validation_plots",
    "generate_validation_report",
    "validate",
]
