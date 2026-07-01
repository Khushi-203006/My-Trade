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
    print(f"\nProcessing: {csv_file.name}")

    #-----------
    #select Top 250 Stocks
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

    #keep only the Top 250 stockes
    df = df.head(250)

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

    # ------------------------
    # Round Values
    # ------------------------
    df = df.round(2)

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
    print("\nColumns Rearranged Successfully!")
    print(df.columns.tolist())
    break
