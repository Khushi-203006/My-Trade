"""
Indicator Engine

Purpose:
    Read cleaned stock data from data/processed/,
    calculate technical indicators,
    and save the enriched data to data/indicators/.

Indicators to be added:
    - Previous Close
    - SMA 9
    - SMA 44
    - SMA 200
    - EMA 20
    - RSI
    - MACD
    - ATR
    - Average Volume (20)
    - Volume Ratio
"""

from pathlib import Path
import pandas as pd
import numpy as np

# -------------------------------
# Project Paths
# -------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_FOLDER = PROJECT_ROOT / "data" / "processed"
INDICATOR_FOLDER = PROJECT_ROOT / "data" / "indicators"

#create output folder if it doesn't exist
INDICATOR_FOLDER.mkdir(parents = True , exist_ok = True)

# -------------------------------
# Read Processed Data
# -------------------------------

def read_data():
    """
    Reads all processed CSV files and combines them into a single DataFrame.
    """

    csv_files = sorted(PROCESSED_FOLDER.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {PROCESSED_FOLDER}"
        )
    
    dataframes = []

    for file in csv_files:
        print(f"Reading: {file.name}")
        df = pd.read_csv(file)
        dataframes.append(df)

    df = pd.concat(dataframes , ignore_index = True)

    #sort by symbol and date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(['Symbol' , 'Date']).reset_index(drop=True)

    print(f"\nTotal rows :{len(df)}")
    print(f"Total stocks : {df['Symbol'].nunique()}")

    return df

def main():
    df = read_data()
    print(df.head())

if __name__ == "__main__":
    main()