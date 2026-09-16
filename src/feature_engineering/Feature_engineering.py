import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PROJECT FOLDERS
# ============================================================

# Find the main project folder
BASE_DIR = Path(__file__).resolve().parents[2]

# Folder containing cleaned NSE daily files
INPUT_FOLDER = BASE_DIR / "data" / "processed"

# File where the final ML features will be stored
OUTPUT_FILE = INPUT_FOLDER / "ml_features.csv"


# ============================================================
# LOAD ALL PROCESSED NSE FILES
# ============================================================

def load_processed_data():
    """
    Read all processed NSE CSV files and combine them
    into one DataFrame.
    """

    csv_files = sorted(
        INPUT_FOLDER.glob("nse_*.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            "No processed NSE files found in data/processed/"
        )

    dataframes = []

    for csv_file in csv_files:

        print(f"Reading: {csv_file.name}")

        df = pd.read_csv(csv_file)

        dataframes.append(df)

    # Combine all daily files
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    return combined_df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):
    """
    Clean and sort the combined data before
    calculating historical features.
    """

    # Convert Date back to datetime
    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    # Remove rows where date or symbol is missing
    df = df.dropna(
        subset=["Date", "Symbol"]
    )

    # Remove exact duplicate market records
    df = df.drop_duplicates(
        subset=[
            "Date",
            "Symbol",
            "Open",
            "High",
            "Low",
            "Close",
            "PrevClose",
            "Volume",
            "TradedValue",
            "Trades"
        ]
    ).copy()

    # Sort by stock first and date second
    df = df.sort_values(
        by=["Symbol", "Date"]
    ).reset_index(drop=True)

    return df


# ============================================================
# CREATE FEATURES
# ============================================================

def create_features(df):
    """
    Create historical features for each stock.

    IMPORTANT:
    All features use CURRENT or PREVIOUS information.
    We do not use future information in the features.
    """

    # --------------------------------------------------------
    # 1. PREVIOUS DAY RETURN
    # --------------------------------------------------------

    df["PreviousReturn"] = (
        df.groupby("Symbol")["DailyReturnPct"]
        .shift(1)
    )


    # --------------------------------------------------------
    # 2. PREVIOUS DAY RANGE
    # --------------------------------------------------------

    df["PreviousRangePct"] = (
        df.groupby("Symbol")["RangePct"]
        .shift(1)
    )


    # --------------------------------------------------------
    # 3. PREVIOUS DAY GAP
    # --------------------------------------------------------

    df["PreviousGapPct"] = (
        df.groupby("Symbol")["GapPct"]
        .shift(1)
    )


    # --------------------------------------------------------
    # 4. THREE-DAY RETURN
    # --------------------------------------------------------

    # Price change compared with the close
    # three trading days earlier.

    df["Return3D"] = (
        df.groupby("Symbol")["Close"]
        .pct_change(periods=3)
        * 100
    )


    # --------------------------------------------------------
    # 5. FIVE-DAY RETURN
    # --------------------------------------------------------

    # Price change compared with the close
    # five trading days earlier.

    df["Return5D"] = (
        df.groupby("Symbol")["Close"]
        .pct_change(periods=5)
        * 100
    )


    # --------------------------------------------------------
    # 6. FIVE-DAY AVERAGE VOLUME
    # --------------------------------------------------------

    # IMPORTANT:
    # shift(1) means today's volume is NOT included.
    #
    # Therefore, when predicting today's movement,
    # this represents the average volume from previous
    # trading days.

    df["AvgVolume5D"] = (
        df.groupby("Symbol")["Volume"]
        .transform(
            lambda x:
            x.shift(1).rolling(5).mean()
        )
    )


    # --------------------------------------------------------
    # 7. VOLUME RATIO
    # --------------------------------------------------------

    # Yesterday's volume divided by the previous
    # five-day average volume.

    previous_volume = (
        df.groupby("Symbol")["Volume"]
        .shift(1)
    )

    df["VolumeRatio"] = (
        previous_volume /
        df["AvgVolume5D"]
    )


    # --------------------------------------------------------
    # 8. FIVE-DAY VOLATILITY
    # --------------------------------------------------------

    # Standard deviation of previous daily returns.

    df["Volatility5D"] = (
        df.groupby("Symbol")["DailyReturnPct"]
        .transform(
            lambda x:
            x.shift(1).rolling(5).std()
        )
    )


    return df


# ============================================================
# CREATE TARGET
# ============================================================

def create_target(df):
    """
    Create the prediction target.

    Target = 1
        if the NEXT trading day's closing price
        is higher than today's closing price.

    Target = 0
        otherwise.
    """

    # Get next trading day's closing price
    df["NextClose"] = (
        df.groupby("Symbol")["Close"]
        .shift(-1)
    )

    # Create binary target
    df["Target"] = (
        df["NextClose"] > df["Close"]
    ).astype(int)

    return df


# ============================================================
# SELECT FINAL ML COLUMNS
# ============================================================

def select_final_columns(df):
    """
    Keep the columns required for machine learning.
    """

    feature_columns = [
        "Date",
        "Symbol",
        "Company",

        # Current market information
        "Open",
        "High",
        "Low",
        "Close",
        "PrevClose",

        # Existing calculated features
        "DailyReturnPct",
        "DailyRange",
        "RangePct",
        "GapPct",

        "Volume",
        "TradedValue",
        "Trades",

        # New features
        "PreviousReturn",
        "PreviousRangePct",
        "PreviousGapPct",
        "Return3D",
        "Return5D",
        "AvgVolume5D",
        "VolumeRatio",
        "Volatility5D",

        # Target
        "Target"
    ]

    return df[feature_columns]


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    print("=" * 60)
    print("FEATURE ENGINEERING STARTED")
    print("=" * 60)


    # --------------------------------------------------------
    # STEP 1: LOAD DATA
    # --------------------------------------------------------

    df = load_processed_data()

    print(
        f"\nTotal rows loaded: {len(df):,}"
    )


    # --------------------------------------------------------
    # STEP 2: PREPARE DATA
    # --------------------------------------------------------

    df = prepare_data(df)


    # --------------------------------------------------------
    # STEP 3: CREATE FEATURES
    # --------------------------------------------------------

    print("\nCreating historical features...")

    df = create_features(df)


    # --------------------------------------------------------
    # STEP 4: CREATE TARGET
    # --------------------------------------------------------

    print("Creating prediction target...")

    df = create_target(df)


    # --------------------------------------------------------
    # STEP 5: REMOVE ROWS WITHOUT ENOUGH HISTORY
    # --------------------------------------------------------

    # The first few rows of each stock cannot have
    # 3-day / 5-day historical features.

    feature_columns = [
        "PreviousReturn",
        "PreviousRangePct",
        "PreviousGapPct",
        "Return3D",
        "Return5D",
        "AvgVolume5D",
        "VolumeRatio",
        "Volatility5D"
    ]

    df = df.dropna(
        subset=feature_columns + ["Target"]
    )


    # --------------------------------------------------------
    # STEP 6: SELECT FINAL COLUMNS
    # --------------------------------------------------------

    df = select_final_columns(df)


    # --------------------------------------------------------
    # STEP 7: SAVE ML DATASET
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        float_format="%.4f"
    )


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FEATURE ENGINEERING COMPLETED")
    print("=" * 60)

    print(
        f"Rows in ML dataset: {len(df):,}"
    )

    print(
        f"Stocks: {df['Symbol'].nunique():,}"
    )

    print(
        f"Date range: "
        f"{df['Date'].min().date()} → "
        f"{df['Date'].max().date()}"
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    print("\nTarget distribution:")

    print(
        df["Target"]
        .value_counts()
        .sort_index()
    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()