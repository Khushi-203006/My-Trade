# =============================================================================
# IMPORT LIBRARIES
# =============================================================================

# Used to connect with Google Sheets
import gspread

# Used for Google Service Account authentication
from oauth2client.service_account import ServiceAccountCredentials

# Used for reading and manipulating CSV files
import pandas as pd

# Used for downloading files from the internet
import requests

# NSE provides the bhavcopy inside a ZIP file
import zipfile

# Allows ZIP files to be read directly from memory
import io

# Used for working with dates
from datetime import datetime, timedelta

# Used for creating folders and reading environment variables
import os

# Used for converting JSON string into Python dictionary
import json


# =============================================================================
# STEP 1 : CONNECT TO GOOGLE SHEETS
# =============================================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Check whether running on GitHub Actions
creds_json = os.environ.get("GCP_CREDENTIALS")

if creds_json:
    # GitHub Actions
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
else:
    # Local computer
    creds = ServiceAccountCredentials.from_json_keyfile_name(
    "../../credentials.json",
    scope
)

# Login to Google Sheets
client = gspread.authorize(creds)


# =============================================================================
# OPEN THE REQUIRED SPREADSHEET
# =============================================================================

spreadsheet_id = "1ibuSpjbCPaRyPM2u0mK3jN_eG3lWqzaz-eVdmbvL4yg"

# Open the worksheet named "Top 250 Stocks"
worksheet = client.open_by_key(spreadsheet_id).worksheet("Top 250 Stocks")


# =============================================================================
# FUNCTION TO DOWNLOAD NSE BHAVCOPY
# =============================================================================

def fetch_bhavcopy_for_date(date_obj):

    # Convert date into YYYYMMDD format
    # Example:
    # 2026-06-22  ---> 20260622
    date_str = date_obj.strftime("%Y%m%d")

    # Create download URL
    url = (
        f"https://nsearchives.nseindia.com/content/cm/"
        f"BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"
    )

    # Fake browser headers
    # Some websites block requests without these headers.
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:

        # Download ZIP file
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        # Continue only if download succeeded
        if response.status_code == 200:

            # Open ZIP directly from memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:

                # ZIP contains only one CSV file
                csv_filename = z.namelist()[0]

                # Open CSV file inside ZIP
                with z.open(csv_filename) as csv_file:

                    # Read CSV into DataFrame
                    df = pd.read_csv(csv_file)

                    # ==========================================================
                    # FIND REQUIRED COLUMN NAMES
                    # Different NSE formats use different column names.
                    # This makes the code work for both old and new formats.
                    # ==========================================================

                    symbol_column = (
                        "TckrSymb"
                        if "TckrSymb" in df.columns
                        else "SYMBOL"
                    )

                    close_column = (
                        "ClsPric"
                        if "ClsPric" in df.columns
                        else "CLOSE"
                    )

                    series_column = (
                        "SctySrs"
                        if "SctySrs" in df.columns
                        else "SERIES"
                    )

                    # Default volume column
                    volume_column = "TtlTradgVol"

                    # Find whichever volume column exists
                    for column in [
                        "TtlTradgVol",
                        "TtlTrdQty",
                        "TotTrdQty",
                        "TOTTRDQTY"
                    ]:
                        if column in df.columns:
                            volume_column = column
                            break

                    # ==========================================================
                    # KEEP ONLY EQ SERIES
                    # Remove ETFs and Liquid Funds
                    # ==========================================================

                    if series_column in df.columns:
                        df = df[
                            df[series_column]
                            .astype(str)
                            .str.strip()
                            == "EQ"
                        ]

                    filter_keywords = (
                        "BEES|ETF|GOLD|LIQUID|CASE|SILVER|LIQ"
                    )

                    df = df[
                        ~df[symbol_column]
                        .astype(str)
                        .str.contains(
                            filter_keywords,
                            case=False,
                            na=False
                        )
                    ]

                    # ==========================================================
                    # SORT BY VOLUME
                    # Keep the full bhavcopy instead of truncating to 250 rows
                    # ==========================================================

                    df_full = (
                        df
                        .sort_values(
                            by=volume_column,
                            ascending=False
                        )
                    )

                    # ==========================================================
                    # SAVE HISTORICAL CSV
                    # ==========================================================

                    os.makedirs(
                        "data/historical",
                        exist_ok=True
                    )

                    file_name = (
                        f"data/historical/"
                        f"nse_{date_obj.strftime('%Y-%m-%d')}.csv"
                    )

                    df_full.to_csv(
                        file_name,
                        index=False
                    )

                    print(
                        f"Saved historical file : {file_name}"
                    )

                    # Return only required columns
                    return df_full[
                        [
                            symbol_column,
                            volume_column,
                            close_column
                        ]
                    ].values.tolist()

        # Download failed
        return None

    except:

        # Any error -> return None
        return None
    

# step - 2 : find latest available trading day

today = datetime.now()

data_to_insert = None

fetched_date = ""

# Check today and previous four working days
for i in range(5):

    current_date = today - timedelta(days=i)

    # Skip Saturday and Sunday
    if current_date.weekday() >= 5:
        continue

    # Try downloading data
    data_to_insert = fetch_bhavcopy_for_date(current_date)

    # Stop if successful
    if data_to_insert:

        fetched_date = current_date.strftime("%d-%b-%Y")
        break



# STEP 3 : UPDATE GOOGLE SHEET

if data_to_insert:

    # Clear old stock list and make room for the full dataset
    worksheet.clear()

    if len(data_to_insert) > 0:
        worksheet.resize(rows=len(data_to_insert) + 1, cols=3)

        # Upload latest data
        worksheet.update(
            "A2",
            data_to_insert
        )
    else:
        print("No data rows available to update the sheet.")

    # Current IST time
    ist_time = (
        datetime.utcnow()
        + timedelta(hours=5, minutes=30)
    ).strftime("%d-%b %H:%M")

    # Status message
    status_message = (
        f"Data Date: {fetched_date}"
        f" | Last Update: {ist_time} (IST)"
    )

    # Write status
    worksheet.update(
        "K2",
        [[status_message]]
    )

    print("SUCCESS : Google Sheet Updated!")