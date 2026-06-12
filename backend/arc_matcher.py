from __future__ import annotations

from typing import Dict

import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean


ARC_TEMPLATES = {
    "Rags to Riches": np.linspace(0.0, 1.0, 20),
    "Tragedy": np.linspace(1.0, 0.0, 20),
    "Icarus": np.concatenate([np.linspace(0.0, 1.0, 8), np.linspace(1.0, 0.0, 12)]),
    "Man in a Hole": np.concatenate([np.linspace(0.7, 0.1, 8), np.linspace(0.1, 0.8, 12)]),
    "Phoenix": np.concatenate([np.linspace(0.5, 0.0, 6), np.linspace(0.0, 1.0, 14)]),
    "Oedipus": np.concatenate([np.linspace(0.8, 0.1, 10), np.linspace(0.1, 0.9, 10)]),
}


def _normalize_segment(segment: list[float]) -> np.ndarray:
    arr = np.asarray(segment, dtype=float)
    if arr.size == 0:
        raise ValueError("Segment must contain at least one point.")
    if np.allclose(arr, arr[0]):
        return np.zeros_like(arr)
    return (arr - arr.min()) / (arr.max() - arr.min())


def generate_arc_templates() -> Dict[str, np.ndarray]:
    return ARC_TEMPLATES.copy()


def match_arc(segment: list[float]) -> dict[str, object]:
    values = _normalize_segment(segment)
    best_arc = None
    best_distance = float("inf")
    raw_scores: dict[str, float] = {}

    for name, template in generate_arc_templates().items():
        distance, _ = fastdtw(values, template, dist=lambda a, b: float(abs(a - b)))
        raw_scores[name] = float(distance)
        if distance < best_distance:
            best_distance = float(distance)
            best_arc = name

    max_distance = max(raw_scores.values()) if raw_scores else 1.0
    confidence = float(1.0 - (best_distance / (max_distance + 1e-6)))
    return {
        "arc_name": best_arc or "Unknown",
        "similarity_score": best_distance,
        "confidence": max(0.0, min(1.0, confidence)),
        "all_scores": raw_scores,
    }
