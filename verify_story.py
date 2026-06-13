"""Verify the enriched fallback story with multi-column data."""
import numpy as np
import pandas as pd
from backend.preprocessor import normalize_timeseries
from backend.narrative import _build_data_summary_story
from backend.changepoint import detect_turning_points
from backend.foundry_iq import get_narrative_template

np.random.seed(42)
n = 500
dates = pd.date_range("2022-01-01", periods=n, freq="D")
steps = np.random.randint(800, 20000, n).astype(float)
df = pd.DataFrame({
    "date": dates,
    "steps": steps,
    "distance_km": steps * 0.0007 + np.random.normal(0, 0.5, n),
    "calories_burned": steps * 0.04 + np.random.normal(0, 20, n),
    "active_minutes": np.random.randint(15, 120, n),
    "sleep_hours": np.random.uniform(5, 9, n),
    "water_intake_liters": np.random.uniform(1, 3.5, n),
    "mood": np.random.choice(["Happy", "Neutral", "Tired", "Stressed", "Energetic"], n),
})

normalized = normalize_timeseries(df)
values = np.asarray(normalized["y_normalized"], dtype=float)
tps = detect_turning_points(values)
foundry = get_narrative_template("Man in a Hole")

meta = normalized["metadata"]
print("=== METADATA ===")
print(f"Y column: {meta['y_column']}")
print(f"X column: {meta['x_column']}")
print(f"Total rows: {meta['total_rows']}")
print(f"Other numeric cols: {meta['other_numeric_columns']}")
print(f"Categorical summaries: {meta.get('categorical_summaries', {})}")
print()

story = _build_data_summary_story(
    "Man in a Hole",
    list(zip(normalized["x_original"], normalized["y_original"])),
    tps, "factual", foundry,
    metadata=meta, x_labels=normalized["x_labels"],
)
print("=== FALLBACK STORY ===")
print(story)
