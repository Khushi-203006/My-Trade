from pathlib import Path

folder = Path(__file__).resolve().parents[2] / "data" / "historical"

for file in folder.glob("*.csv"):
    name = file.stem

    if "_" in name and not name.startswith("nse"):
        day,month,year = name.split("_")
        new_name = f"nse_{year}-{month.zfill(2)}-{day.zfill(2)}.csv"
        file.rename(folder / new_name)

print("Done!")