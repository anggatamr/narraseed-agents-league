from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

logger = logging.getLogger(__name__)


def parse_csv_robust(df: pd.DataFrame) -> tuple[list[tuple[float, float]], list[str], dict[str, Any]]:
    """Intelligently parse a DataFrame into time-series data.
    
    Detects entity/categorical columns for filtering, date/time columns for sorting,
    and numeric columns for value target.
    """
    entity_col = None
    entity_val = None
    potential_entity_cols = ["entity", "code", "country", "state", "category", "group", "name"]
    for col in df.columns:
        if col.lower() in potential_entity_cols:
            entity_col = col
            break
            
    if entity_col is not None:
        counts = df[entity_col].value_counts()
        valid_entities = counts[counts >= 5].index.tolist()
        if valid_entities:
            entity_val = valid_entities[0]
            df = df[df[entity_col] == entity_val].copy()
            
    x_col = None
    x_labels = []
    
    potential_time_cols = ["date", "time", "year", "month", "week", "day", "timestamp", "semester", "period"]
    for col in df.columns:
        if col.lower() in potential_time_cols:
            x_col = col
            break
            
    if x_col is None:
        for col in df.columns:
            col_dtype = str(df[col].dtype)
            is_string_like = (
                df[col].dtype == object
                or col_dtype == "string"
                or col_dtype == "str"
                or isinstance(df[col].dtype, pd.DatetimeTZDtype)
            )
            if is_string_like:
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    if parsed.notna().sum() > 0.8 * len(df):
                        x_col = col
                        break
                except:
                    pass

    if x_col is not None:
        x_dtype_str = str(df[x_col].dtype)
        is_date_like = (
            x_col.lower() in ["date", "time", "timestamp"]
            or df[x_col].dtype == object
            or x_dtype_str == "string"
            or x_dtype_str == "str"
        )
        if is_date_like:
            df['__parsed_time__'] = pd.to_datetime(df[x_col], errors='coerce')
            df = df.dropna(subset=['__parsed_time__'])
            df = df.sort_values('__parsed_time__')
            x_labels = df[x_col].astype(str).tolist()
            df = df.drop(columns=['__parsed_time__'])
        else:
            df = df.sort_values(x_col)
            x_labels = df[x_col].astype(str).tolist()
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            x_col = numeric_cols[0]
            df = df.sort_values(x_col)
            x_labels = [f"Point {i}" for i in range(len(df))]
        else:
            x_labels = [f"Point {i}" for i in range(len(df))]
            
    y_col = None
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if x_col in numeric_cols:
        numeric_cols.remove(x_col)
        
    if numeric_cols:
        y_col = numeric_cols[0]
    else:
        for col in df.columns:
            if col != x_col:
                try:
                    df[col] = df[col].astype(float)
                    y_col = col
                    break
                except:
                    pass
                    
    if y_col is None:
        raise ValueError("No numeric data columns found in the CSV.")

    x_vals = list(range(len(df)))
    y_vals = df[y_col].astype(float).tolist()
    data_points = list(zip(x_vals, y_vals))

    # Capture summary stats for ALL numeric columns (multi-column context)
    other_numeric_cols = [c for c in numeric_cols if c != y_col]
    numeric_summaries: dict[str, dict[str, float]] = {}
    for col in numeric_cols:
        col_vals = df[col].astype(float).dropna()
        if len(col_vals) > 0:
            numeric_summaries[col] = {
                "mean": float(col_vals.mean()),
                "min": float(col_vals.min()),
                "max": float(col_vals.max()),
                "std": float(col_vals.std()) if len(col_vals) > 1 else 0.0,
            }

    # Capture categorical columns (e.g. mood)
    categorical_summaries: dict[str, list[str]] = {}
    for col in df.columns:
        if col == x_col:
            continue
        is_categorical = (
            df[col].dtype == object
            or str(df[col].dtype) == "string"
            or str(df[col].dtype) == "str"
            or (hasattr(df[col].dtype, "name") and "string" in str(df[col].dtype.name).lower())
        )
        if is_categorical:
            try:
                top_vals = df[col].value_counts().head(5).index.tolist()
                if top_vals:
                    categorical_summaries[col] = [str(v) for v in top_vals]
            except Exception:
                pass

    metadata = {
        "x_column": x_col or "Index",
        "y_column": y_col,
        "entity_column": entity_col,
        "entity_value": entity_val,
        "all_numeric_columns": numeric_cols,
        "other_numeric_columns": other_numeric_cols,
        "numeric_summaries": numeric_summaries,
        "categorical_summaries": categorical_summaries,
        "total_rows": len(df),
        "message": f"Parsed X from '{x_col or 'Index'}', Y from '{y_col}'" + (f" (filtered by {entity_col}='{entity_val}')" if entity_val else "")
    }

    return data_points, x_labels, metadata


def normalize_timeseries(
    data: list[tuple[float, float]] | pd.DataFrame | str,
    gpr_smooth: bool = False,
    gpr_kernel: Any = None,
) -> dict[str, Any]:
    """Load time-series data and normalize values to [0, 1].

    Args:
        data: Either a list of (x, y) tuples, a pandas DataFrame, or a CSV file path.
        gpr_smooth: If True, compute smoothed values using Gaussian Process.
        gpr_kernel: Optional kernel for GaussianProcessRegressor.

    Returns:
        A dictionary with normalized and original data, plus stats.
    """
    x_labels = []
    metadata = {}
    
    if isinstance(data, str):
        df = pd.read_csv(data)
        data_points, x_labels, metadata = parse_csv_robust(df)
        x, y = zip(*data_points)
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
    elif isinstance(data, pd.DataFrame):
        data_points, x_labels, metadata = parse_csv_robust(data)
        x, y = zip(*data_points)
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
    else:
        if not data:
            raise ValueError("Input data cannot be empty.")
        x, y = zip(*data)
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        x_labels = [str(val) for val in x]
        metadata = {"x_column": "X", "y_column": "Y", "message": "Parsed direct values"}

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
        "x_labels": x_labels,
        "metadata": metadata,
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

