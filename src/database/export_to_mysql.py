import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine , text , inspect

# ============================================================
# CONNECT TO MYSQL SERVER
# ============================================================

# Connect only to the MySQL Server.
# We are NOT connecting to any database yet because
# the database may not exist.

DB_USER = "root"
DB_PASSWORD = "khushi"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "trade"
# Base name for all stock tables.
# Tables will be named:
# stock_table_1
# stock_table_2
# stock_table_3
BASE_TABLE_NAME = "stock_table"

# Maximum number of rows allowed in one table.
MAX_ROWS_PER_TABLE = 10_000_000

server_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
)

print("Connected to MySQL server successfully.")

# ============================================================
# CREATE DATABASE IF IT DOES NOT EXIST
# ============================================================

# Open a connection to the MySQL Server.

with server_engine.connect() as conn:
    # Create the database only if it doesn't already exist.
    # If the database already exists, MySQL simply ignores this command.

    conn.execute(
        text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    )

    #Save the changes
    conn.commit()

print(f"Database '{DB_NAME}' is ready.")

# ============================================================
# CONNECT TO THE DATABASE
# ============================================================

# Now that the database is guaranteed to exist,
# create a new connection engine that points to the
# 'trade' database.

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print(f"Connected to database '{DB_NAME}' successfully.")

# ============================================================
# FIND THE CURRENT ACTIVE TABLE
# ============================================================

# Create an inspector object.
# It is used to get information about the database.
inspector = inspect(engine)

#Get the names of all tables present in the database
all_tables = inspector.get_table_names()

#keep only tables that start with "stock_table"
stock_tables = sorted(
    [
        table for table in all_tables
        if table.startswith(f"{BASE_TABLE_NAME}_")
    ]
)
# ------------------------------------------------------------
# CASE 1
# No stock table exists.
#
# The first table will be:
#
# stock_table_1
# ------------------------------------------------------------

if len(stock_tables) == 0:

    current_table = f"{BASE_TABLE_NAME}_1"

    print(f"No stock table found.")
    print(f"{current_table} will be created automatically.")

# ------------------------------------------------------------
# CASE 2
# Tables already exist.
#
# Example:
#
# stock_table_1
# stock_table_2
#
# The newest table becomes the active table.
# ------------------------------------------------------------

else:
    current_table = stock_tables[-1]
    print(f"Current active table: {current_table}")


'''
# Import the pandas library.
# It is used for reading CSV files and working with data in DataFrames.
import pandas as pd

# Import Path from pathlib.
# Path makes it easier to work with folders and file paths.
from pathlib import Path

# Import SQLAlchemy functions.
# create_engine -> Creates a connection to the MySQL database.
# text -> Allows us to write SQL queries safely.
from sqlalchemy import create_engine , text , inspect

#------------------------
# Database Configuration
#------------------------

DB_USER = "root"
DB_PASSWORD = "khushi"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "trade"
TABLE_NAME = "stock_table"


# ============================================================
# CREATE DATABASE CONNECTION
# ============================================================

# Create a connection engine.
# The engine is used later to execute SQL queries and insert data.
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
)

with engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    conn.commit()

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create an inspector object to inspect the database.
inspector = inspect(engine)

# Check whether the table already exists.
table_exists = inspector.has_table(TABLE_NAME)

df.to_sql(
    TABLE_NAME,
    con=engine,
    if_exists="append",
    index=False
)

if table_exists:
    print(f"{TABLE_NAME} already exists.")
else:
    print(f"{TABLE_NAME} does not exist.")
    print("The table will be created automatically when the first CSV is imported.")


#------------------------
# DATA FOLDER
#------------------------

# Path of the processed CSV files.
# Example:
# D:\Khushi\my trade\data\processed
DATA_FOLDER = Path(r"D:\Khushi\my trade\data\processed")

#------------------------
# IMPORT FILES
#------------------------

# This will find every file whose name starts with "nse_"
# Example:
# nse_2026-07-24.csv
# nse_2026-07-25.csv
# nse_2026-07-26.csv

# sorted() ensures the files are processed in order.
for csv_file in sorted(DATA_FOLDER.glob("nse_*.csv")):

    # --------------------------------------------------------
    # Extract the date from the filename.
    #
    # csv_file.stem returns the filename without ".csv"
    #
    # Example:
    # nse_2026-07-24
    #
    # replace("nse_", "")
    #
    # becomes
    #
    # 2026-07-24
    # --------------------------------------------------------
    
    file_date = csv_file.stem.replace("nse_" , "")

    # ========================================================
    # CHECK WHETHER THIS DATE IS ALREADY IN THE DATABASE
    # ========================================================

    # SQL query
    #
    # Count how many rows exist for this date.
    #
    # If count > 0
    # then this day's data has already been imported.

    query = text(
        f"""
    select count(*)
    from {TABLE_NAME}
    WHERE Date = :date
    """
    )

    # Open a temporary connection to the database.
    with engine.connect() as conn:

        # Execute the SQL query.
        #
        # :date is replaced with file_date.
        #
        # Example:
        #
        # SELECT COUNT(*)
        # FROM stock_table
        # WHERE Date='2026-07-24'
        #
        # scalar() returns the single value produced by COUNT(*).
        count = conn.execute(query, {"date": file_date}).scalar()


    # ========================================================
    # IF DATA ALREADY EXISTS
    # ========================================================

    if count > 0:
        print(f"Skipped : {csv_file.name} (Already Imported)")
        continue

    # If execution reaches here,
    # it means this CSV has NOT been imported before.

    print(f"Importing : {csv_file.name}")
    df = pd.read_csv(csv_file)

    # ========================================================
    # INSERT DATA INTO MYSQL
    # ========================================================

    # to_sql() inserts the DataFrame into the database.
    #
    # if_exists="append"
    #
    # means:
    # Add new rows to the existing table.
    #
    # Do NOT delete existing rows.
    #
    # index=False
    #
    # prevents pandas from inserting DataFrame index as a column.
    try:
        df.to_sql(
            TABLE_NAME,
            con=engine,
            if_exists="append",
            index=False
        )
        print(f"Imported : {len(df)} rows")

    except Exception as e:
        print(f"Error importing {csv_file.name}: {e}")


# ============================================================
# FINISHED
# ============================================================

print("\nAll files have been checked.")
print("Database is up to date.")
'''