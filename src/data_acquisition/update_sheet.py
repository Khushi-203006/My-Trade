import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime, timedelta
import os
import json

# 1. Credentials Setup

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = os.environ.get("GCP_CREDENTIALS")

if creds_json:
    # Running on GitHub Actions
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
else:
    # Running on local computer
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    credentials_path = os.path.join(project_root, "credentials.json")

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        credentials_path,
        scope
)

client = gspread.authorize(creds)
# Open Google Sheet
spreadsheet_id = "1ibuSpjbCPaRyPM2u0mK3jN_eG3lWqzaz-eVdmbvL4yg"

worksheet = client.open_by_key(
    spreadsheet_id
).worksheet("BhavStock List")

# 2. NSE UDiFF Data Fetcher
def fetch_bhavcopy_for_date(date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    df = pd.read_csv(f)
                    
                    sym_col = 'TckrSymb' if 'TckrSymb' in df.columns else 'SYMBOL'
                    close_col = 'ClsPric' if 'ClsPric' in df.columns else 'CLOSE'
                    series_col = 'SctySrs' if 'SctySrs' in df.columns else 'SERIES'
                    
                    vol_col = 'TtlTradgVol'
                    for c in ['TtlTradgVol', 'TtlTrdQty', 'TotTrdQty', 'TOTTRDQTY']:
                        if c in df.columns:
                            vol_col = c
                            break
                    
                    # सिर्फ EQ सीरीज और ETFs (LIQUID/BEES) को बाहर करना
                    if series_col in df.columns:
                        df = df[df[series_col].astype(str).str.strip() == 'EQ']
                    filter_keywords = 'BEES|ETF|GOLD|LIQUID|CASE|SILVER|LIQ'
                    df = df[~df[sym_col].astype(str).str.contains(filter_keywords, case=False, na=False)]
                    
                df_top = df.sort_values(by=vol_col, ascending=False)

                # Save complete Bhavcopy locally
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(script_dir))

                historical_folder = os.path.join(project_root, "data", "historical")

                os.makedirs(historical_folder, exist_ok=True)

                filename = os.path.join(
                    historical_folder,
                    f"nse_{date_obj.strftime('%Y-%m-%d')}.csv"
                )

                df_top.to_csv(filename, index=False)

                print(f"Saved: {filename}")

                return df_top[[sym_col, vol_col, close_col]].values.tolist()
                
        return None
    except Exception as e:
        print(e)
        return None

# 3. Execution Logic
date = datetime.now()
data_to_insert = None
fetched_date_str = ""

for i in range(5): 
    test_date = date - timedelta(days=i)
    if test_date.weekday() >= 5: continue
        
    data_to_insert = fetch_bhavcopy_for_date(test_date)
    if data_to_insert:
        fetched_date_str = test_date.strftime('%d-%b-%Y')
        break

# 4. Update Sheet
if data_to_insert:
    worksheet.batch_clear(['A:C'])
    worksheet.update('A2', data_to_insert)
    ist_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d-%b %H:%M')
    status_msg = f"Data Date: {fetched_date_str} | Last Update: {ist_now} (IST)"
    worksheet.update('G2', [[status_msg]])
    print("SUCCESS: Sheet Updated!")