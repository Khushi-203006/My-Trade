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
# CREATE IMPORT HISTORY TABLE
# ============================================================

with engine.connect() as conn:

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS import_history (

            FileName VARCHAR(255) PRIMARY KEY,

            FileDate DATE NOT NULL,

            ImportedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """))

    conn.commit()

print("Import history table is ready.")

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

# ============================================================
# CHECK WHETHER THE CURRENT TABLE HAS REACHED THE ROW LIMIT
# ============================================================

# If the current table does not exist yet,
# there is nothing to check.
if current_table in all_tables:

    # SQL query to count the number of rows
    query = text(
        f"""
        SELECT COUNT(*)
        FROM {current_table}
        """
    )

    # Execute the query
    with engine.connect() as conn:
        row_count = conn.execute(query).scalar()

    print(f"{current_table} contains {row_count:,} rows.")

    # --------------------------------------------------------
    # Check whether the table has reached the maximum limit.
    # --------------------------------------------------------

    if row_count >= MAX_ROWS_PER_TABLE:

        # Extract the table number.
        #
        # Example:
        #
        # stock_table_3
        #
        # becomes
        #
        # 3

        table_number = int(current_table.split("_")[-1])

        # Next table
        #
        # stock_table_4

        current_table = f"{BASE_TABLE_NAME}_{table_number + 1}"

        print(f"Row limit reached.")
        print(f"Switching to {current_table}")

else:

    print(f"{current_table} will be created when the first CSV is imported.")

# ============================================================
# IMPORT ALL PROCESSED CSV FILES
# ============================================================

DATA_FOLDER = Path(r"D:\Khushi\my trade\data\processed")

for csv_file in sorted(DATA_FOLDER.glob("nse_*.csv")):

    # Extract date
    file_date = csv_file.stem.replace("nse_", "")

    # ------------------------------------------------------------
    # Check whether the current table has reached its row limit.
    # If yes, switch to the next table.
    # ------------------------------------------------------------

    if current_table in all_tables:

        with engine.connect() as conn:
            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {current_table}")
            ).scalar()

        if row_count >= MAX_ROWS_PER_TABLE:
            table_number = int(current_table.split("_")[-1])
            current_table = f"{BASE_TABLE_NAME}_{table_number + 1}"
            print(f"Row limit reached. Switching to {current_table}")

    # ============================================================
    # CHECK IMPORT HISTORY
    # ============================================================

    with engine.connect() as conn:
        count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM import_history
                WHERE FileName = :filename
            """),
            {"filename": csv_file.name}
        ).scalar()

    if count > 0:
        print(f"Skipped : {csv_file.name} (Already Imported)")
        continue

    # ============================================================
    # CHECK WHETHER THIS DATE ALREADY EXISTS IN ANY STOCK TABLE
    # ============================================================

    already_imported = False

    with engine.connect() as conn:
        for table in stock_tables:
            count = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE Date = :date
                    """
                ),
                {"date": file_date}
            ).scalar()

            if count > 0:
                already_imported = True
                print(
                    f"Skipped : {csv_file.name} "
                    f"(Already imported in {table})"
                )
                break

    if already_imported:
        continue

    # Read CSV only if it hasn't already been imported
    df = pd.read_csv(csv_file)

    try:
        df.to_sql(
            current_table,
            con=engine,
            if_exists="append",
            index=False
        )

        print(f"Imported : {len(df)} rows")

        # ============================================================
        # SAVE IMPORT INFORMATION
        # ============================================================

        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO import_history
                    (FileName, FileDate)
                    VALUES
                    (:filename, :filedate)
                """),
                {
                    "filename": csv_file.name,
                    "filedate": file_date
                }
            )
            conn.commit()

    except Exception as e:
        print(f"Error importing {csv_file.name}: {e}")

# print total numbers of records in all stock tables
total_records = 0
for table in stock_tables:
    with engine.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar()
        total_records += count

print(f"Total records across all stock tables: {total_records:,}")