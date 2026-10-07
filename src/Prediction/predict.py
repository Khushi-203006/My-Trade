import pandas as pd
import joblib
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import text

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

PREDICTION_DIR = (
    BASE_DIR
    / "data"
    / "predictions"
)

PREDICTION_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# MYSQL CONNECTION
# ============================================================

DB_USER = "root"
DB_PASSWORD = "khushi"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "stock_prediction"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("Connected to prediction database successfully.")

# ============================================================
# FEATURES USED BY THE MODEL
# ============================================================

with engine.begin() as connection:
    connection.execute(
        text("DELETE FROM todays_prediction")
    )

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
# ADD PREDICTION RANK
# ============================================================

top10["prediction_rank"] = range(1, len(top10) + 1)


# ============================================================
# SAVE TOP 10 TO MYSQL
# ============================================================

mysql_data = top10.rename(
    columns={
        "Date": "prediction_date",
        "Symbol": "symbol",
        "Company": "company",
        "Close": "close_price",
        "Probability_UP": "probability_up",
        "Predicted": "predicted"
    }
)

mysql_data.to_sql(
    "todays_prediction",
    con=engine,
    if_exists="append",
    index=False
)

print("\nTop 10 predictions saved to MySQL.")

# ============================================================
# SAVE DAILY PREDICTION FILE
# ============================================================

output_file = (
    PREDICTION_DIR
    / f"prediction_{latest_date.strftime('%Y-%m-%d')}.csv"
)

top10.to_csv(
    output_file,
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
print(output_file)

print("\n" + "=" * 60)
print("PREDICTION COMPLETED")
print("=" * 60)