import pandas as pd
import pickle
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "ml_features.csv"
MODEL_FILE = BASE_DIR / "src" / "Prediction" / "model.pkl"


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
    f"{df['Date'].min().date()} → {df['Date'].max().date()}"
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "PreviousReturn",
    "PreviousRangePct",
    "PreviousGapPct",
    "Return3D",
    "Return5D",
    "AvgVolume5D",
    "VolumeRatio",
    "Volatility5D"
]

TARGET = "Target"


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df = df.sort_values("Date").reset_index(drop=True)


# ============================================================
# TIME-BASED TRAIN / TEST SPLIT
# ============================================================

split_date = df["Date"].quantile(0.80)

train_df = df[df["Date"] <= split_date].copy()
test_df = df[df["Date"] > split_date].copy()

print("\nTime-based split:")
print(f"Training data: {len(train_df):,} rows")
print(f"Testing data : {len(test_df):,} rows")

print(
    f"Training dates: "
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


# ============================================================
# TRAIN RANDOM FOREST
# ============================================================

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=10,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

print("Model training completed.")


# ============================================================
# PREDICTION
# ============================================================

print("\nEvaluating model...")

y_pred = model.predict(X_test)
# Probability of the stock going UP
y_probability = model.predict_proba(X_test)[:, 1]

test_results = test_df[
    ["Date", "Symbol", "Company", "Close", "Target"]
].copy()

test_results["Predicted"] = y_pred
test_results["Probability_UP"] = y_probability

print("\nPrediction probability analysis:")

for threshold in [0.50, 0.60, 0.70, 0.80]:
    selected = test_results[
        test_results["Probability_UP"] >= threshold
    ]

    if len(selected) > 0:
        precision = (
            selected["Target"].mean() * 100
        )

        print(
            f"Probability >= {threshold:.2f} | "
            f"Stocks: {len(selected):,} | "
            f"UP precision: {precision:.2f}%"
        )
    else:
        print(
            f"Probability >= {threshold:.2f} | "
            f"No predictions"
        )

# ============================================================
# MODEL EVALUATION
# ============================================================

accuracy = accuracy_score(y_test, y_pred)

print("\n" + "=" * 60)
print("MODEL RESULTS")
print("=" * 60)

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["DOWN / NOT UP", "UP"]
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))


# ============================================================
# SAVE MODEL
# ============================================================

with open(MODEL_FILE, "wb") as file:
    pickle.dump(model, file)

print("\n" + "=" * 60)
print("MODEL SAVED")
print("=" * 60)

print(f"\nSaved to:")
print(MODEL_FILE)

print("\nMODEL TRAINING COMPLETED")