import pandas as pd  #filter, modify, read, save and sort CSV file
from pathlib import Path #helps working with file and folder paths
import numpy as np

def add_calculated_columns(df):

    #add calculated columns to the dataframe

    prev_close = df["PrevClose"].replace(0, np.nan) # replace 0 with NaN to avoid division by zero
    open_price = df["Open"].replace(0,np.nan) #replace 0 with NaN to avoid division by zero

    #Daily Return (%)
    df["DailyReturnPct"] = (
        (df["Close"] - prev_close)/ prev_close
    ) * 100

    #Daily Range
    df["DailyRange"] = (
        df["High"] - df["Low"]
    )

    #Range Percentage
    df["RangePct"] = (
        (df["DailyRange"]) / open_price
    ) * 100

    #Gap Percentage
    df["GapPct"] = (
        (open_price - prev_close) / prev_close
    ) * 100

    return df

def rearrange_columns(df):
    #Rearrange columns into a fixed order

    column_order = [
        "Date",
        "Symbol",
        "Company",
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
        "Trades"
    ]
    return df[column_order]

#------------
#Project Folders
#------------
#project root folder
BASE_DIR = Path(__file__).resolve ().parents[2]

#raw data folder
INPUT_FOLDER = BASE_DIR / "data" / "historical"

#processed data folder
OUTPUT_FOLDER = BASE_DIR/"data" / "processed"

#Create processed folderif it doesn't exist
OUTPUT_FOLDER.mkdir(parents = True , exist_ok = True)


#Read every CSV file from the historical folder
for csv_file in INPUT_FOLDER.glob("*.csv"):  #glob("*.csv") -> means find every file ending with .csv
    output_file = OUTPUT_FOLDER / csv_file.name

    if output_file.exists():
        try:
            existing_date = pd.read_csv(
                output_file,
                usecols=["Date"],
                nrows=1
            )["Date"].iloc[0]
            expected_date = pd.Timestamp(
                csv_file.stem.removeprefix("nse_")
            )
            if pd.Timestamp(existing_date).normalize() == expected_date:
                continue
            print(f"Reprocessing stale file: {csv_file.name}")
        except (ValueError, IndexError, KeyError):
            print(f"Reprocessing invalid file: {csv_file.name}")

    print(f"\nProcessing pending file: {csv_file.name}")

    #-----------
    # Load full bhavcopy data
    #-----------

    #Read CSV into a DataFrames
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()

    # print(df.columns.tolist())

    for col in ["TtlTradgVol", "TTL_TRD_QNTY", "TtlTrdQty", "TotTrdQty", "TOTTRDQTY", "Volume"]:
        if col in df.columns:
            volume_column = col
            break
    else:
        raise ValueError("Volume column not found!")

    #sort by trading volume (Highest to lowest)
    df = df.sort_values(by = volume_column , ascending=False)

    # Keep all rows from the bhavcopy instead of truncating to the top 250

    #Temprary columns
    #print(df.head(10))
    #break

    # ------------------------
    # Rename Columns
    # ------------------------

    rename_dict = {

        # Date
        "TradDt": "Date",
        "DATE1": "Date",

        # Symbol
        "TckrSymb": "Symbol",
        "SYMBOL": "Symbol",

        # Company
        "FinInstrmNm": "Company",
        "NAME OF COMPANY": "Company",

        # Prices
        "OpnPric": "Open",
        "OPEN": "Open",
        "OPEN_PRICE": "Open",

        "HghPric": "High",
        "HIGH": "High",
        "HIGH_PRICE": "High",

        "LwPric": "Low",
        "LOW": "Low",
        "LOW_PRICE": "Low",

        "ClsPric": "Close",
        "CLOSE": "Close",
        "CLOSE_PRICE": "Close",

        "PrvsClsgPric": "PrevClose",
        "PREVCLOSE": "PrevClose",
        "PREV_CLOSE": "PrevClose",

        # Volume
        "TtlTradgVol": "Volume",
        "TTL_TRD_QNTY": "Volume",

        # Traded Value
        "TtlTrfVal": "TradedValue",
        "TTL_TRD_VAL": "TradedValue",
        "TURNOVER_LACS": "TradedValue",

        # Trades
        "TtlNbOfTxsExctd": "Trades",
        "NO_OF_TRADES": "Trades"
    }

    # print("\nBefore Rename:")
    # print(df.columns.tolist())

    df.rename(columns=rename_dict, inplace=True)

    if "Company" not in df.columns and "Symbol" in df.columns:
        df["Company"] = df["Symbol"]

    # print("\nAfter Rename:")
    # print(df.columns.tolist())

    # ------------------------
    # Keep Required Columns
    # ------------------------

    required_columns = [
        "Date",
        "Symbol",
        "Company",
        "Open",
        "High",
        "Low",
        "Close",
        "PrevClose",
        "Volume",
        "TradedValue",
        "Trades"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns after rename: {missing_columns}")

    df = df[required_columns]

    # ------------------------
    # Convert Date to MySQL format
    # ------------------------

    # NSE files use ISO dates (YYYY-MM-DD). An explicit format prevents
    # pandas from interpreting 2026-09-01 as 2026-01-09.
    df["Date"] = pd.to_datetime(
        df["Date"],
        format="mixed",
        dayfirst=False,
        errors="coerce"
    )

    if df["Date"].isna().any():
        print(f"Skipping {csv_file.name}: invalid date found")
        continue

    expected_date = pd.Timestamp(csv_file.stem.removeprefix("nse_"))
    if not (df["Date"].dt.normalize() == expected_date).all():
        print(
            f"Skipping {csv_file.name}: source date does not match "
            f"filename date {expected_date.date()}"
        )
        continue

    # Convert to MySQL DATETIME format
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Temporary Check - For required columns
    # print("\nTemporary Check - Code is working till required columns step")
    # print(f"Rows after top 250 filter: {len(df)}")
    # print("Final Columns:")
    # print(df.columns.tolist())
    # print("Sample Data:")
    # print(df.head())

    # # Uncomment while testing only first file
    # break

    df = add_calculated_columns(df)

    # Temporary Check - For calculated columns
   
    # print("\nCalculated Columns Added Successfully!")
    # print(df[[
    # "Symbol",
    # "DailyReturnPct",
    # "DailyRange",
    # "RangePct",
    # "GapPct"
    # ]].head())

    # Uncomment while testing only first file
    # break

    # ------------------------
    # Rearrange Columns
    # ------------------------
    df = rearrange_columns(df)

    # Temporary Check
    # print("\nColumns Rearranged Successfully!")
    # print(df.columns.tolist())
    # break

    # ------------------------
    # Round Values
    # ------------------------

    decimal_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "PrevClose",
        "DailyReturnPct",
        "DailyRange",
        "RangePct",
        "GapPct",
        "TradedValue"
    ]

    df[decimal_columns] = df[decimal_columns].round(2)

    # ------------------------
    # Rearrange Columns
    # ------------------------

    df = rearrange_columns(df)

    # ------------------------
    # Save Processed CSV
    # ------------------------

    try:
        df.to_csv(
            output_file,
            index=False,
            float_format="%.2f"
        )
    except PermissionError:
        print(
            f"Could not update {output_file.name}: file is locked. "
            "Close the file and run the cleaner again."
        )
        continue

    print(f"Saved successfully: {output_file.name}")