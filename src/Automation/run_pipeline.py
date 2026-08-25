import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import threading
import pyautogui
import time

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
# TKINTER WINDOW SETUP
# ============================================================

root = tk.Tk()

root.title("My-Trade Automation Pipeline")
root.geometry("700x430")
root.resizable(False, False)

#Title
title_label = tk.Label(root, 
                       text="My-Trade Automation Pipeline", 
                       font=("Segoe UI", 18, "bold")
                    )
title_label.pack(pady = (20, 15))

#Main text area
output = tk.Text(
    root,
    width = 78,
    height = 20,
    font = ("Consolas" , 11),
    state = "disabled",
    padx = 15,
    pady = 15
)

output.pack(padx = 20 , pady=5)

# ============================================================
# FUNCTIONS
# ============================================================
def write_output(text):
    output.config(state = "normal")
    output.insert(tk.END , text + "\n")
    output.see(tk.END)
    output.config(state="disabled")

def run_command(command):

    result = subprocess.run(
        command,
        cwd = PROJECT_DIR,
        text = True,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    return result

def pipeline():
    try:
        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        write_output(
            "Step 1: Pulling latest files from GitHub..."
        )
        result = run_command(
            ["git","pull","--no-edit","origin","main"]
        )

        if result.returncode != 0:
            raise Exception(
                "Step 1 failed:\n" + result.stderr
            )

        write_output(
            "Step 1: Pulling latest files from GitHub completed"
        )

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------
        write_output(
            "step 2: Running clean_data.py..."
        )

        result = run_command(
            [str(PYTHON_EXE), str(CLEAN_SCRIPT)]
        )

        if result.returncode != 0:
            raise Exception(
                "Step 2 failed:\n" + result.stderr
            )

        write_output(
            "Step 2: Running data cleaning - COMPLETED"
        )

        # ----------------------------------------------------
        # STEP 3
        # ----------------------------------------------------

        write_output(
            "Step 3: Importing data into MySQL..."
        )

        result = run_command(
            [str(PYTHON_EXE), str(DB_SCRIPT)]
        )

        if result.returncode != 0:
            raise Exception(
                "Step 3 failed: \n" + result.stderr
            )

        write_output(
            "Step 3: Importing data into MySQL - COMPLETED"
        )

        # ----------------------------------------------------
        # STEP 4
        # ----------------------------------------------------

        write_output("Step 4 : Updating GitHub repository...")
        write_output("Adding files to Git...")

        write_output("    git add .")

        result = run_command(
            ["git", "add", "."]
        )

        if result.returncode != 0:
            raise Exception(
                "Git add failed:\n" + result.stderr
            )


        write_output(
            '    git commit -m "Automated commit from pipeline"'
        )

        result = run_command(
            [
                "git",
                "commit",
                "-m",
                "Automated commit from pipeline"
            ]
        )

        
        # Exit code 1 can mean "nothing to commit".
        # That is not necessarily an error.
        if result.returncode != 0:

            combined_output = (
                result.stdout + result.stderr
            ).lower()

            if "nothing to commit" not in combined_output:
                raise Exception(
                    "Git commit failed:\n" + result.stderr
                )

            write_output(
                "    Nothing new to commit."
            )

        write_output(
            "    git push origin main"
        )

        result = run_command(
            ["git", "push", "origin", "main"]
        )

        if result.returncode != 0:
            raise Exception(
                "Git push failed:\n" + result.stderr
            )

        write_output("")
        write_output(
            "Step 4: Updating GitHub - COMPLETED"
        )

        write_output("")
        write_output("=" * 60)
        write_output(
            "PIPELINE COMPLETED SUCCESSFULLY"
        )
        write_output("=" * 60)

        write_output("")
        write_output("Press ENTER to close this window.")

        root.bind("<Return>", close_window)

    except Exception as e:

        write_output("=" * 60)
        write_output("PIPELINE FAILED")
        write_output("=" * 60)
        write_output("")
        write_output(str(e))
        write_output("")
        write_output("Press ENTER to close this window.")

        root.bind("<Return>", close_window)


def close_window(event=None):
    root.destroy()

# Start pipeline in background so the Tkinter window remains
# responsive while the commands are running.
threading.Thread(
    target=pipeline,
    daemon=True
).start()


# Start GUI
root.mainloop()

# ============================================================
# START PIPELINE
# ============================================================
        
'''        
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
    main()'''