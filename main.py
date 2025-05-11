import os
import subprocess
import sys
import venv

VENV_DIR = "venv"

# Step 1: Create the virtual environment if it doesn't exist
if not os.path.exists(VENV_DIR):
    print("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)

# Step 2: Define the pip executable in the venv
pip_path = os.path.join(VENV_DIR, "bin", "pip")
python_path = os.path.join(VENV_DIR, "bin", "python")

# On Windows, adjust paths
if os.name == "nt":
    pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")

# Step 3: Install dependencies
print("Installing dependencies...")
subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
subprocess.check_call([pip_path, "install", "google-api-python-client", "google-auth",
                       "google-auth-httplib2", "google-auth-oauthlib", "PyPDF2"])

# Step 4: Run test.py using the virtual environment
print("Running test.py...")
subprocess.check_call([python_path, "test.py"])
