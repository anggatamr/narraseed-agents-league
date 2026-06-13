"""Test end-to-end with a realistic 500-row steps tracker CSV."""
import io
import numpy as np
import pandas as pd
import requests

np.random.seed(42)
n = 500
dates = pd.date_range("2022-01-01", periods=n, freq="D")
steps = np.random.randint(5000, 20000, n)
distance_km = steps * 0.0007 + np.random.normal(0, 0.5, n)
calories = steps * 0.04 + np.random.normal(0, 20, n)
active_min = steps / 200 + np.random.normal(0, 10, n)
sleep_hrs = np.random.normal(7, 1, n).clip(3, 11)
water = np.random.normal(2.5, 0.5, n).clip(0.5, 5)
moods = np.random.choice(["Happy", "Tired", "Energetic", "Stressed", "Calm"], n)

df = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"),
    "steps": steps,
    "distance_km": np.round(distance_km, 1),
    "calories_burned": np.round(calories, 1),
    "active_minutes": np.round(active_min, 0).astype(int),
    "sleep_hours": np.round(sleep_hrs, 1),
    "water_intake_liters": np.round(water, 2),
    "mood": moods,
})

csv_buf = io.BytesIO(df.to_csv(index=False).encode())
files = {"file": ("steps_tracker.csv", csv_buf, "text/csv")}
data = {"style": "dramatic"}

print("Sending 500-row steps tracker to /api/analyze ...")
r = requests.post("http://localhost:8000/api/analyze", files=files, data=data, timeout=120)
result = r.json()

print("\n=== STORY ===")
print(result["story"])

print("\n=== METADATA ===")
meta = result.get("metadata", {})
print(f"total_rows: {meta.get('total_rows')}")
print(f"numeric_summaries keys: {list(meta.get('numeric_summaries', {}).keys())}")
print(f"categorical_summaries: {meta.get('categorical_summaries')}")
print(f"other_numeric_columns: {meta.get('other_numeric_columns')}")

print("\n=== ARC ===")
print(f"Arc: {result.get('arc')}")
print(f"Turning points: {len(result.get('turning_points', []))}")
