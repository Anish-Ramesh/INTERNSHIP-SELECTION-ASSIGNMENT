import subprocess
import sys
import os

def setup():
    """
    One-command setup for the Movie Reasoning Agent.
    1. Installs dependencies from requirements.txt
    2. Runs the data preprocessing pipeline.
    """
    print("\n" + "="*60)
    print(" MOVIE REASONING AGENT: ONE-COMMAND SETUP ".center(60, "="))
    print("="*60)

    # 1. Create Virtual Environment
    print(f"\n[1/3] Creating virtual environment (venv)...")
    try:
        if not os.path.exists("venv"):
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print(">>> SUCCESS: venv created.")
        else:
            print(">>> venv already exists. Skipping creation.")
    except Exception as e:
        print(f"!!! Error creating venv: {e}")
        return

    # Determine venv python path
    if os.name == "nt": # Windows
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    else: # Unix/MacOS
        venv_python = os.path.join("venv", "bin", "python")

    # 2. Install Dependencies
    print(f"\n[2/3] Installing dependencies into venv...")
    try:
        subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
        print(">>> SUCCESS: Dependencies installed.")
    except Exception as e:
        print(f"!!! Error installing dependencies: {e}")
        print(">>> Proceeding to preprocessing...")

    # 3. Run Preprocessing
    print(f"\n[3/3] Running data preprocessing pipeline...")
    if not os.path.exists("preprocess.py"):
        print("!!! Error: preprocess.py not found in root.")
        return

    try:
        subprocess.check_call([venv_python, "preprocess.py"])
        print(">>> SUCCESS: Data indices and SQLite database initialized.")
    except Exception as e:
        print(f"!!! Error during preprocessing: {e}")
        return

    print("\n" + "="*60)
    print(" SETUP COMPLETE ".center(60, "="))
    print("="*60)
    print("\nYou can now run the agent (ensure venv is activated):")
    print("  Windows: .\\venv\\Scripts\\activate")
    print("  MacOS/Linux: source venv/bin/activate")
    print("  python agent/agent_loop.py")
    print("\nOr run the evaluation suite:")
    print("  python task_D_20eval_test.py")

if __name__ == "__main__":
    setup()
