import pandas as pd  #filter, modify, read, save and sort CSV file
from pathlib import Path #helps working with file and folder paths

#project root folder
BASE_DIR = Path(__file__).resolve ().parents[2]

#raw data folder
INPUT_FOLDER = BASE_DIR / "data" / "historical"

#processed data folder
OUTPUT_FOLDER = BASE_DIR/"data" / "processed"

#Create processed folderif it doesn't exist
OUTPUT_FOLDER.mkdir(parents = True , exist_ok = True)



