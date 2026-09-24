import pandas as pd
import pickle
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
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


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("MODEL TRAINING STARTED")
print("=" * 60)

print("\nLoading ML dataset...")

df = pd.read_csv(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

print(f"Rows loaded: {len(df):,}")
print(f"Stocks: {df['Symbol'].nunique():,}")

print(
    f"Date range: "
    f"{df['Date'].min().date()} → "
    f"{df['Date'].max().date()}"
)


# ============================================================
# FEATURES
# ============================================================

# These are the 20 features created by
# feature_engineering.py

FEATURES = [

    # Previous-day features
    "PreviousReturn",
    "PreviousRangePct",
    "PreviousGapPct",

    # Momentum
    "Return3D",
    "Return5D",
    "Return10D",

    # Moving averages
    "SMA5",
    "SMA10",
    "PriceVsSMA5",
    "PriceVsSMA10",

    # Volume
    "AvgVolume5D",
    "AvgVolume10D",
    "VolumeRatio",
    "VolumeTrend",

    # Volatility
    "Volatility5D",
    "Volatility10D",

    # Price range
    "High5D",
    "Low5D",
    "PricePosition5D"
]

TARGET = "Target"


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

print("\nChecking required columns...")

required_columns = FEATURES + [TARGET]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("\nERROR: Missing columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Required ML columns are missing from ml_features.csv"
    )

print("All required columns are present.")


# ============================================================
# REMOVE MISSING / INVALID VALUES
# ============================================================

print("\nChecking data quality...")

df = df.replace(
    [float("inf"), float("-inf")],
    pd.NA
)

before_rows = len(df)

df = df.dropna(
    subset=FEATURES + [TARGET]
).copy()

after_rows = len(df)

print(
    f"Rows removed because of missing values: "
    f"{before_rows - after_rows:,}"
)

print(
    f"Rows available for training/testing: "
    f"{after_rows:,}"
)


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df = df.sort_values(
    "Date"
).reset_index(drop=True)


# ============================================================
# TIME-BASED TRAIN / TEST SPLIT
# ============================================================

# IMPORTANT:
# We do NOT randomly split stock-market data.
#
# Older data -> Training
# Newer data -> Testing
#
# This better represents how the model will work
# in the real world.

split_date = df["Date"].quantile(0.80)

train_df = df[
    df["Date"] <= split_date
].copy()

test_df = df[
    df["Date"] > split_date
].copy()


print("\n" + "=" * 60)
print("TIME-BASED TRAIN / TEST SPLIT")
print("=" * 60)

print(f"\nSplit date: {split_date.date()}")

print(
    f"Training data: "
    f"{len(train_df):,} rows"
)

print(
    f"Testing data : "
    f"{len(test_df):,} rows"
)

print(
    f"\nTraining dates: "
    f"{train_df['Date'].min().date()} → "
    f"{train_df['Date'].max().date()}"
)

print(
    f"Testing dates : "
    f"{test_df['Date'].min().date()} → "
    f"{test_df['Date'].max().date()}"
)


# ============================================================
# PREPARE X AND Y
# ============================================================

X_train = train_df[FEATURES]

y_train = train_df[TARGET]

X_test = test_df[FEATURES]

y_test = test_df[TARGET]


print("\nTraining features:", X_train.shape)

print("Testing features :", X_test.shape)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\nTraining Target Distribution:")

print(
    y_train.value_counts()
    .sort_index()
)

print("\nTesting Target Distribution:")

print(
    y_test.value_counts()
    .sort_index()
)


# ============================================================
# TRAIN RANDOM FOREST
# ============================================================

print("\n" + "=" * 60)
print("TRAINING RANDOM FOREST")
print("=" * 60)

model = RandomForestClassifier(

    # Number of decision trees
    n_estimators=200,

    # Maximum depth of each tree
    max_depth=12,

    # Minimum samples required at a leaf
    min_samples_leaf=10,

    # Makes results reproducible
    random_state=42,

    # Use all available CPU cores
    n_jobs=-1,

    # Helps deal with target imbalance
    class_weight="balanced"
)


print("\nTraining model...")

model.fit(
    X_train,
    y_train
)

print("Model training completed.")


# ============================================================
# PREDICTION
# ============================================================

print("\nEvaluating model...")

# Normal class prediction
y_pred = model.predict(X_test)


# Probability that the stock goes UP
y_probability = model.predict_proba(
    X_test
)[:, 1]


# ============================================================
# CREATE TEST RESULTS TABLE
# ============================================================

test_results = test_df[
    [
        "Date",
        "Symbol",
        "Company",
        "Close",
        "Target"
    ]
].copy()

test_results["Predicted"] = y_pred

test_results["Probability_UP"] = y_probability

# ============================================================
# SAVE TEST PREDICTIONS
# ============================================================

TEST_PREDICTIONS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "test_predictions.csv"
)

test_results.to_csv(
    TEST_PREDICTIONS_FILE,
    index=False
)

print("\nTest predictions saved to:")

print(TEST_PREDICTIONS_FILE)

# ============================================================
# PROBABILITY ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("PREDICTION PROBABILITY ANALYSIS")
print("=" * 60)

print(
    "\nThis shows how accurate the model is when we "
    "only consider predictions above different confidence levels."
)


for threshold in [
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80
]:

    selected = test_results[
        test_results["Probability_UP"] >= threshold
    ]

    if len(selected) > 0:

        precision = (
            selected["Target"].mean()
            * 100
        )

        print(
            f"\nProbability >= {threshold:.2f}"
        )

        print(
            f"Stocks selected : "
            f"{len(selected):,}"
        )

        print(
            f"UP precision    : "
            f"{precision:.2f}%"
        )

    else:

        print(
            f"\nProbability >= {threshold:.2f}"
            f" | No predictions"
        )


# ============================================================
# MODEL EVALUATION
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)


print("\n" + "=" * 60)
print("MODEL RESULTS")
print("=" * 60)


print(
    f"\nAccuracy: "
    f"{accuracy * 100:.2f}%"
)


# ------------------------------------------------------------
# Classification Report
# ------------------------------------------------------------

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "DOWN / NOT UP",
            "UP"
        ]
    )
)


# ------------------------------------------------------------
# Confusion Matrix
# ------------------------------------------------------------

print("\nConfusion Matrix:")

cm = confusion_matrix(
    y_test,
    y_pred
)

print(cm)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({

    "Feature": FEATURES,

    "Importance":
        model.feature_importances_

})


importance = importance.sort_values(
    "Importance",
    ascending=False
)


print("\n" + "=" * 60)
print("FEATURE IMPORTANCE")
print("=" * 60)

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\nSaving trained model...")

with open(
    MODEL_FILE,
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


print("\n" + "=" * 60)
print("MODEL SAVED")
print("=" * 60)

print("\nSaved to:")

print(MODEL_FILE)

print("\n" + "=" * 60)
print("MODEL TRAINING COMPLETED")
print("=" * 60)