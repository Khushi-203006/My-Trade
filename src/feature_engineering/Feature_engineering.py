import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "ml_features.csv"


# ============================================================
# 1. LOAD ALL PROCESSED NSE FILES
# ============================================================

def load_all_data():
    """
    Load all processed NSE CSV files and combine them
    into one DataFrame.
    """

    files = sorted(PROCESSED_DIR.glob("nse_*.csv"))

    if not files:
        print("ERROR: No processed NSE files found.")
        return pd.DataFrame()

    dataframes = []

    print("\nLoading processed files...")

    for file in files:

        try:
            df = pd.read_csv(file)

            if df.empty:
                continue

            dataframes.append(df)

            print(f"Loaded: {file.name} | Rows: {len(df)}")

        except Exception as e:
            print(f"ERROR reading {file.name}: {e}")

    if not dataframes:
        print("ERROR: No valid data loaded.")
        return pd.DataFrame()

    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    print("\nTotal rows loaded:", len(combined_df))

    return combined_df


# ============================================================
# 2. PREPARE DATA
# ============================================================

def prepare_data(df):
    """
    Clean and prepare data before feature engineering.
    """

    print("\nPreparing data...")

    # --------------------------------------------------------
    # Convert Date column
    # --------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove rows with missing Date or Symbol
    # --------------------------------------------------------

    df = df.dropna(
        subset=["Date", "Symbol"]
    ).copy()

    # --------------------------------------------------------
    # Remove duplicate market records
    #
    # A stock should have only one record for a
    # particular trading day.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Sort by stock and date
    #
    # This is VERY important because all rolling and
    # previous-day calculations depend on chronological order.
    # --------------------------------------------------------

    df = df.sort_values(
        ["Symbol", "Date"]
    ).reset_index(drop=True)

    print("Rows after cleaning:", len(df))

    print(
        "Duplicate Symbol-Date rows:",
        df.duplicated(
            subset=["Symbol", "Date"]
        ).sum()
    )

    print(
        "Stocks:",
        df["Symbol"].nunique()
    )

    return df


# ============================================================
# 3. CREATE FEATURES
# ============================================================

def create_features(df):
    """
    Create historical features used by the ML model.

    IMPORTANT:
    Every feature uses information available BEFORE
    the prediction day.

    This prevents future-data leakage.
    """

    print("\nCreating features...")

    # --------------------------------------------------------
    # Previous Day Return
    # --------------------------------------------------------

    df["PreviousReturn"] = (
        df.groupby("Symbol")["DailyReturnPct"]
        .shift(1)
    )

    # --------------------------------------------------------
    # Previous Day Range
    # --------------------------------------------------------

    df["PreviousRangePct"] = (
        df.groupby("Symbol")["RangePct"]
        .shift(1)
    )

    # --------------------------------------------------------
    # Previous Day Gap
    # --------------------------------------------------------

    df["PreviousGapPct"] = (
        df.groupby("Symbol")["GapPct"]
        .shift(1)
    )

    # --------------------------------------------------------
    # 3-Day Return
    # --------------------------------------------------------

    df["Return3D"] = (
        df.groupby("Symbol")["Close"]
        .transform(
            lambda x: (
                x.shift(1) /
                x.shift(4) - 1
            ) * 100
        )
    )

    # --------------------------------------------------------
    # 5-Day Return
    # --------------------------------------------------------

    df["Return5D"] = (
        df.groupby("Symbol")["Close"]
        .transform(
            lambda x: (
                x.shift(1) /
                x.shift(6) - 1
            ) * 100
        )
    )

    # --------------------------------------------------------
    # 10-Day Return
    # --------------------------------------------------------

    df["Return10D"] = (
        df.groupby("Symbol")["Close"]
        .transform(
            lambda x: (
                x.shift(1) /
                x.shift(11) - 1
            ) * 100
        )
    )

    # ========================================================
    # MOVING AVERAGES
    # ========================================================

    # --------------------------------------------------------
    # 5-Day SMA
    # --------------------------------------------------------

    df["SMA5"] = (
        df.groupby("Symbol")["Close"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(5)
            .mean()
        )
    )

    # --------------------------------------------------------
    # 10-Day SMA
    # --------------------------------------------------------

    df["SMA10"] = (
        df.groupby("Symbol")["Close"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(10)
            .mean()
        )
    )

    # --------------------------------------------------------
    # Current Price vs SMA5
    #
    # Positive = price above recent average
    # Negative = price below recent average
    # --------------------------------------------------------

    df["PriceVsSMA5"] = (
        (df["Close"] - df["SMA5"])
        / df["SMA5"].replace(0, np.nan)
        * 100
    )

    # --------------------------------------------------------
    # Current Price vs SMA10
    # --------------------------------------------------------

    df["PriceVsSMA10"] = (
        (df["Close"] - df["SMA10"])
        / df["SMA10"].replace(0, np.nan)
        * 100
    )

    # ========================================================
    # VOLUME FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Average Volume - 5 Days
    # --------------------------------------------------------

    df["AvgVolume5D"] = (
        df.groupby("Symbol")["Volume"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(5)
            .mean()
        )
    )

    # --------------------------------------------------------
    # Average Volume - 10 Days
    # --------------------------------------------------------

    df["AvgVolume10D"] = (
        df.groupby("Symbol")["Volume"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(10)
            .mean()
        )
    )

    # --------------------------------------------------------
    # Volume Ratio
    #
    # Previous day's volume compared with the
    # average volume of the previous 5 days.
    # --------------------------------------------------------

    previous_volume = (
        df.groupby("Symbol")["Volume"]
        .shift(1)
    )

    df["VolumeRatio"] = (
        previous_volume /
        df["AvgVolume5D"].replace(0, np.nan)
    )

    # --------------------------------------------------------
    # Volume Trend
    #
    # 5-day average volume compared with
    # 10-day average volume.
    # --------------------------------------------------------

    df["VolumeTrend"] = (
        df["AvgVolume5D"] /
        df["AvgVolume10D"].replace(0, np.nan)
    )

    # ========================================================
    # VOLATILITY FEATURES
    # ========================================================

    # --------------------------------------------------------
    # 5-Day Volatility
    # --------------------------------------------------------

    df["Volatility5D"] = (
        df.groupby("Symbol")["DailyReturnPct"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(5)
            .std()
        )
    )

    # --------------------------------------------------------
    # 10-Day Volatility
    # --------------------------------------------------------

    df["Volatility10D"] = (
        df.groupby("Symbol")["DailyReturnPct"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(10)
            .std()
        )
    )

    # ========================================================
    # PRICE RANGE FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Highest price during previous 5 days
    # --------------------------------------------------------

    df["High5D"] = (
        df.groupby("Symbol")["High"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(5)
            .max()
        )
    )

    # --------------------------------------------------------
    # Lowest price during previous 5 days
    # --------------------------------------------------------

    df["Low5D"] = (
        df.groupby("Symbol")["Low"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(5)
            .min()
        )
    )

    # --------------------------------------------------------
    # Position of current close inside previous 5-day range
    #
    # 0   = near the lowest price
    # 1   = near the highest price
    # --------------------------------------------------------

    price_range = (
        df["High5D"] - df["Low5D"]
    )

    df["PricePosition5D"] = (
        (df["Close"] - df["Low5D"])
        /
        price_range.replace(0, np.nan)
    )

    print("Feature creation completed.")

    return df


# ============================================================
# 4. CREATE TARGET
# ============================================================

def create_target(df):
    """
    Create the prediction target.

    Target = 1
        if the NEXT trading day's closing price
        is higher than today's closing price.

    Target = 0
        if the NEXT trading day's closing price
        is not higher.

    The last available row for each stock is removed
    because its future closing price is unknown.
    """

    print("\nCreating target...")

    # --------------------------------------------------------
    # Get next trading day's closing price
    # --------------------------------------------------------

    df["NextClose"] = (
        df.groupby("Symbol")["Close"]
        .shift(-1)
    )

    # --------------------------------------------------------
    # Create target
    #
    # 1 = next day's Close > today's Close
    # 0 = next day's Close <= today's Close
    # --------------------------------------------------------

    df["Target"] = (
        df["NextClose"] > df["Close"]
    ).astype("float")

    # --------------------------------------------------------
    # Last row of each stock has no future price.
    #
    # Do NOT incorrectly classify it as 0.
    # --------------------------------------------------------

    df.loc[
        df["NextClose"].isna(),
        "Target"
    ] = np.nan

    print("Target created.")

    return df


# ============================================================
# 5. SELECT FINAL COLUMNS
# ============================================================

def select_final_columns(df):
    """
    Select the columns required for ML training.

    This keeps:
    - Original market data
    - Engineered features
    - Target
    """

    print("\nSelecting final columns...")

    final_columns = [

        # ----------------------------------------------------
        # Identification
        # ----------------------------------------------------

        "Date",
        "Symbol",
        "Company",

        # ----------------------------------------------------
        # Original market data
        # ----------------------------------------------------

        "Open",
        "High",
        "Low",
        "Close",
        "PrevClose",

        "DailyReturnPct",
        "DailyRange",
        "RangePct",
        "GapPct",

        "Volume",
        "TradedValue",
        "Trades",

        # ----------------------------------------------------
        # Previous-day features
        # ----------------------------------------------------

        "PreviousReturn",
        "PreviousRangePct",
        "PreviousGapPct",

        # ----------------------------------------------------
        # Momentum features
        # ----------------------------------------------------

        "Return3D",
        "Return5D",
        "Return10D",

        # ----------------------------------------------------
        # Moving average features
        # ----------------------------------------------------

        "SMA5",
        "SMA10",
        "PriceVsSMA5",
        "PriceVsSMA10",

        # ----------------------------------------------------
        # Volume features
        # ----------------------------------------------------

        "AvgVolume5D",
        "AvgVolume10D",
        "VolumeRatio",
        "VolumeTrend",

        # ----------------------------------------------------
        # Volatility features
        # ----------------------------------------------------

        "Volatility5D",
        "Volatility10D",

        # ----------------------------------------------------
        # Price range features
        # ----------------------------------------------------

        "High5D",
        "Low5D",
        "PricePosition5D",

        # ----------------------------------------------------
        # Target
        # ----------------------------------------------------

        "Target"
    ]

    # Check whether any required column is missing

    missing_columns = [
        column
        for column in final_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Missing columns:")

        for column in missing_columns:
            print(" -", column)

        raise ValueError(
            "Some required columns are missing."
        )

    return df[final_columns].copy()


# ============================================================
# 6. MAIN PIPELINE
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("MY-TRADE FEATURE ENGINEERING")
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 1
    # Load data
    # --------------------------------------------------------

    df = load_all_data()

    if df.empty:
        return

    # --------------------------------------------------------
    # STEP 2
    # Prepare data
    # --------------------------------------------------------

    df = prepare_data(df)

    # --------------------------------------------------------
    # STEP 3
    # Create features
    # --------------------------------------------------------

    df = create_features(df)

    # --------------------------------------------------------
    # STEP 4
    # Create target
    # --------------------------------------------------------

    df = create_target(df)

    # ========================================================
    # REQUIRED ML FEATURES
    # ========================================================

    feature_columns = [

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

    # --------------------------------------------------------
    # Remove rows that do not have enough historical data
    # --------------------------------------------------------
    
    df = df.dropna(
        subset=feature_columns + ["Target"]
    ).copy()

    # --------------------------------------------------------
    # Remove infinite values if any
    # --------------------------------------------------------

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    df = df.dropna(
        subset=feature_columns + ["Target"]
    ).copy()

    # --------------------------------------------------------
    # Convert Target to integer
    # --------------------------------------------------------

    df["Target"] = (
        df["Target"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Select final columns
    # --------------------------------------------------------

    df = select_final_columns(df)

    # --------------------------------------------------------
    # Sort final dataset
    # --------------------------------------------------------

    df = df.sort_values(
        ["Date", "Symbol"]
    ).reset_index(drop=True)

    # ========================================================
    # VALIDATION
    # ========================================================

    print("\n")
    print("=" * 70)
    print("FINAL DATASET VALIDATION")
    print("=" * 70)

    print(
        "Rows:",
        len(df)
    )

    print(
        "Stocks:",
        df["Symbol"].nunique()
    )

    print(
        "Date range:",
        df["Date"].min().date(),
        "to",
        df["Date"].max().date()
    )

    print(
        "Duplicate Symbol-Date rows:",
        df.duplicated(
            subset=["Symbol", "Date"]
        ).sum()
    )

    print("\nTarget distribution:")

    print(
        df["Target"]
        .value_counts()
        .sort_index()
    )

    print("\nMissing values:")

    missing_values = (
        df.isna()
        .sum()
    )

    missing_values = (
        missing_values[
            missing_values > 0
        ]
    )

    if missing_values.empty:
        print("No missing values.")

    else:
        print(missing_values)

    # ========================================================
    # SAVE
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n")
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)

    print(
        f"ML features saved to:\n{OUTPUT_FILE}"
    )

    print(
        "\nFinal columns:"
    )

    for column in df.columns:
        print(" -", column)

    print("\nFeature engineering completed successfully.")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()