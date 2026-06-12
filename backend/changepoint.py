from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def _severity(value_before: float, value_after: float) -> float:
    """Compute severity of change (0-1, normalized)."""
    return float(min(1.0, abs(value_after - value_before)))


def _simple_pelt_pure_python(values: np.ndarray, pen: float = 3.0) -> list[int]:
    """
    Pure-Python changepoint detection using simple segmentation.
    
    Detects significant changes in time series by:
    1. Computing first-order differences
    2. Identifying high-magnitude changes (above threshold)
    3. Filtering adjacent changes to avoid noise
    
    Args:
        values: 1D array of normalized values
        pen: penalty factor (scales threshold; higher = fewer changepoints)
    
    Returns:
        List of breakpoint indices
    """
    n = len(values)
    if n < 3:
        return []
    
    # Compute first-order differences (derivative approximation)
    diffs = np.abs(np.diff(values))
    
    # Adaptive threshold: median + penalty * std
    median_diff = float(np.median(diffs)) if len(diffs) > 0 else 0.0
    std_diff = float(np.std(diffs)) if len(diffs) > 0 else 0.1
    threshold = median_diff + (pen * 0.1) * std_diff
    
    # Find indices where difference exceeds threshold
    high_changes = np.where(diffs > threshold)[0] + 1
    
    if len(high_changes) == 0:
        return []
    
    # Filter: keep only non-adjacent changes (min gap = 2 indices)
    breakpoints = [int(high_changes[0])]
    for idx in high_changes[1:]:
        if idx - breakpoints[-1] >= 2:
            breakpoints.append(int(idx))
    
    # Add end-of-series as implicit breakpoint
    if breakpoints[-1] != n - 1:
        breakpoints.append(n)
    
    return breakpoints


def detect_turning_points(values: np.ndarray, pen: float = 3.0) -> list[dict[str, float]]:
    """
    Detect turning points in a normalized time series using pure-Python algorithm.
    
    Args:
        values: 1D numpy array of normalized time series values
        pen: penalty factor for changepoint detection (default 3.0)
    
    Returns:
        List of dicts with keys: index, severity, direction, value_before, value_after
    """
    if values.ndim != 1:
        raise ValueError("Input values must be a 1D numpy array.")
    if len(values) < 3:
        return []

    # Detect breakpoints
    breakpoints = _simple_pelt_pure_python(values, pen=pen)
    
    points: list[dict[str, float]] = []
    previous = 0
    
    for bp in breakpoints:
        if bp <= previous or bp >= len(values):
            previous = bp
            continue
        
        # Use segment mean for before/after comparison
        segment_before = values[previous:bp]
        segment_after_start = min(bp + 1, len(values) - 1)
        segment_after = values[segment_after_start:min(segment_after_start + (bp - previous), len(values))]
        
        value_before = float(np.mean(segment_before)) if len(segment_before) > 0 else float(values[previous])
        value_after = float(np.mean(segment_after)) if len(segment_after) > 0 else float(values[bp - 1])
        
        direction = "growth" if value_after > value_before else "decline"
        if abs(value_after - value_before) < 1e-3:
            direction = "transition"
        
        points.append(
            {
                "index": float(bp - 1),
                "severity": _severity(value_before, value_after),
                "direction": direction,
                "value_before": value_before,
                "value_after": value_after,
                "original_value_before": value_before,
                "original_value_after": value_after,
            }
        )
        previous = bp

    logger.debug("Detected %d turning points", len(points))
    return points
