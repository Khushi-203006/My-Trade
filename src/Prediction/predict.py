import pandas as pd
import joblib
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml_features.csv"
)

MODEL_FILE = (
    BASE_DIR
    / "src"
    / "Prediction"
    / "model.pkl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "todays_prediction.csv"
)


# ============================================================
# FEATURES USED BY THE MODEL
# ============================================================

FEATURES = [
    "PreviousReturn",
    "PreviousRangePct",
    "PreviousGapPct",
    "Return3D",
    "Return5D",
    "Return10D",
    "SMA5",
    "SMA10",
    "PriceVsSMA5",
    "PriceVsSMA10",
    "AvgVolume5D",
    "AvgVolume10D",
    "VolumeRatio",
    "VolumeTrend",
    "Volatility5D",
    "Volatility10D",
    "High5D",
    "Low5D",
    "PricePosition5D"
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING DATA")
print("=" * 60)

df = pd.read_csv(FEATURE_FILE)

df["Date"] = pd.to_datetime(df["Date"])

latest_date = df["Date"].max()

latest_data = df[df["Date"] == latest_date].copy()

print("Latest date:", latest_date.date())
print("Stocks available:", len(latest_data))


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")


# ============================================================
# GENERATE PREDICTIONS
# ============================================================

X = latest_data[FEATURES]

latest_data["Probability_UP"] = model.predict_proba(X)[:, 1]

latest_data["Predicted"] = (
    latest_data["Probability_UP"] >= 0.50
).astype(int)


# ============================================================
# KEEP HIGH-CONFIDENCE PREDICTIONS
# ============================================================

predictions = latest_data[
    latest_data["Probability_UP"] >= 0.60
].copy()


# ============================================================
# SORT BY PROBABILITY
# ============================================================

predictions = predictions.sort_values(
    "Probability_UP",
    ascending=False
)


# ============================================================
# TAKE TOP 10
# ============================================================

top10 = predictions.head(10).copy()


# ============================================================
# SELECT OUTPUT COLUMNS
# ============================================================

top10 = top10[
    [
        "Date",
        "Symbol",
        "Company",
        "Close",
        "Probability_UP",
        "Predicted"
    ]
]


# ============================================================
# SAVE OUTPUT
# ============================================================

top10.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 60)
print("TODAY'S TOP 10 PREDICTIONS")
print("=" * 60)

print(
    top10.to_string(index=False)
)

print("\nPrediction file saved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("PREDICTION COMPLETED")
print("=" * 60)