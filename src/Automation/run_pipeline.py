import subprocess
import sys
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_DIR = Path(r"D:\Khushi\my trade")

# Python executable from your virtual environment
PYTHON_EXE = PROJECT_DIR / "venv" / "Scripts" / "python.exe"

# Script paths
CLEAN_SCRIPT = PROJECT_DIR / "src" / "data_processing" / "clean_data.py"
DB_SCRIPT = PROJECT_DIR / "src" / "database" / "export_to_mysql.py"


# ============================================================
# FUNCTION TO RUN COMMANDS
# ============================================================

def run_command(command, description):
    print("\n" + "=" * 60)
    print(f"{description}")
    print("=" * 60)

    result = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        text=True
    )

    if result.returncode != 0:
        print(f"\n❌ {description} Failed")
        sys.exit(1)

    print(f"✅ {description} Completed")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    # --------------------------------------------------------
    # STEP 1 : Git Pull
    # --------------------------------------------------------

    run_command(
        ["git", "pull","--no-edit", "origin", "main"],
        "STEP 1 : Pulling latest files from GitHub"
    )

    # --------------------------------------------------------
    # STEP 2 : Clean Data
    # --------------------------------------------------------

    run_command(
        [str(PYTHON_EXE), str(CLEAN_SCRIPT)],
        "STEP 2 : Running clean_data.py"
    )

    # --------------------------------------------------------
    # STEP 3 : Import into Database
    # --------------------------------------------------------

    run_command(
        [str(PYTHON_EXE), str(DB_SCRIPT)],
        "STEP 3 : Importing data into MySQL"
    )

    # --------------------------------------------------------
    # STEP 4 : Push data to Git
    # --------------------------------------------------------

    run_command(
        ["git", "add", "."],
        "STEP 4 : Adding files to Git"
    )

    run_command(
        ["git", "commit", "-m", "Automated commit from pipeline"],
        "STEP 5 : Committing changes to Git"
    )

    run_command(
        
        ["git", "push", "origin", "main"],
        "STEP 6 : Pushing changes to GitHub"
    )

    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
if __name__ == "__main__":
    main()