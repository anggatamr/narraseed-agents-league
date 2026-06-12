from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

logger = logging.getLogger(__name__)


def normalize_timeseries(
    data: list[tuple[float, float]] | str,
    gpr_smooth: bool = False,
    gpr_kernel: Any = None,
) -> dict[str, Any]:
    """Load time-series data and normalize values to [0, 1].

    Args:
        data: Either a list of (x, y) tuples or a CSV file path.
        gpr_smooth: If True, compute smoothed values using Gaussian Process.
        gpr_kernel: Optional kernel for GaussianProcessRegressor.

    Returns:
        A dictionary with normalized and original data, plus stats.
    """
    if isinstance(data, str):
        df = pd.read_csv(data)
        if df.shape[1] < 2:
            raise ValueError("CSV must contain at least two columns.")
        x = df.iloc[:, 0].astype(float).to_numpy()
        y = df.iloc[:, 1].astype(float).to_numpy()
    else:
        if not data:
            raise ValueError("Input data cannot be empty.")
        x, y = zip(*data)
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

    if len(x) < 2:
        raise ValueError("At least two data points are required.")

    # Handle missing values via linear interpolation
    series = pd.Series(y)
    if series.isna().any():
        series = series.interpolate(method="linear", limit_direction="both")
        y = series.to_numpy(dtype=float)

    y_min = float(np.nanmin(y))
    y_max = float(np.nanmax(y))
    if np.isclose(y_max, y_min):
        y_normalized = np.zeros_like(y)
    else:
        y_normalized = (y - y_min) / (y_max - y_min)

    x_min = float(np.nanmin(x))
    x_max = float(np.nanmax(x))
    if np.isclose(x_max, x_min):
        x_normalized = np.linspace(0.0, 1.0, len(x))
    else:
        x_normalized = (x - x_min) / (x_max - x_min)

    result = {
        "x_normalized": x_normalized.tolist(),
        "y_normalized": y_normalized.tolist(),
        "x_original": x.tolist(),
        "y_original": y.tolist(),
        "stats": {
            "min": y_min,
            "max": y_max,
            "mean": float(np.mean(y)),
            "n_points": int(len(y)),
        },
    }

    if gpr_smooth:
        kernel = gpr_kernel or (RBF(length_scale=1.0) + WhiteKernel(noise_level=1.0))
        model = GaussianProcessRegressor(kernel=kernel, alpha=0.0)
        x_fit = x.reshape(-1, 1)
        model.fit(x_fit, y)
        y_smooth, y_std = model.predict(x_fit, return_std=True)
        if np.isclose(y_max, y_min):
            y_smooth_norm = np.zeros_like(y_smooth)
        else:
            y_smooth_norm = (y_smooth - y_min) / (y_max - y_min)
        result["y_smooth"] = y_smooth_norm.tolist()
        result["y_std"] = y_std.tolist()

    logger.debug("Normalized %d points", len(y))
    return result
