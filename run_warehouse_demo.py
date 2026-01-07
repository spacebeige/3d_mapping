#!/usr/bin/env python3
"""
Cross-platform launcher for warehouse_demo.ipynb
Works on Windows, macOS, and Linux
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Error: Python 3.9 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} found")

def check_notebook_exists():
    """Check if notebook file exists"""
    notebook_path = Path("examples/warehouse_demo.ipynb")
    if not notebook_path.exists():
        print("❌ Error: warehouse_demo.ipynb not found")
        print("   Please run this script from the repository root directory")
        sys.exit(1)
    print("✓ Found warehouse_demo.ipynb")

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    
    try:
        if requirements_file.exists():
            print("   Installing from requirements.txt...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
                check=True
            )
            print("✓ Dependencies installed from requirements.txt")
        else:
            print("   Installing core dependencies...")
            packages = [
                "numpy", "pandas", "plotly", "scikit-learn", 
                "ipywidgets", "ipython", "pydantic", "networkx", "jupyter"
            ]
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + packages + ["--quiet"],
                check=True
            )
            print("✓ Core dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Some dependencies may not have installed correctly")
        print(f"   Error: {e}")

def check_jupyter():
    """Check if Jupyter is installed"""
    try:
        subprocess.run(
            [sys.executable, "-m", "jupyter", "--version"],
            check=True,
            capture_output=True
        )
        print("✓ Jupyter is ready")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   Installing Jupyter...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "jupyter", "--quiet"],
                check=True
            )
            print("✓ Jupyter installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error: Failed to install Jupyter")
            return False

def enable_ipywidgets():
    """Enable ipywidgets extension"""
    print("\n🔧 Enabling ipywidgets extension...")
    try:
        subprocess.run(
            [sys.executable, "-m", "jupyter", "nbextension", "enable", 
             "--py", "widgetsnbextension", "--sys-prefix"],
            capture_output=True
        )
        print("✓ ipywidgets extension enabled")
    except subprocess.CalledProcessError:
        print("   (extension may already be enabled)")

def launch_jupyter():
    """Launch Jupyter Notebook"""
    print_header("Setup Complete!")
    
    print("📝 Instructions:\n")
    print("1. The Jupyter Notebook will open in your browser")
    print("2. Click 'Cell' → 'Run All' to run the entire notebook")
    print("3. Or use Shift+Enter to run cells one at a time")
    print("4. Interact with the widgets as they appear\n")
    print("📖 For detailed instructions, see examples/README.md\n")
    
    input("Press Enter to launch Jupyter Notebook...")
    
    print("\n🚀 Launching Jupyter Notebook...\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "jupyter", "notebook", 
             "examples/warehouse_demo.ipynb"],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n✓ Jupyter Notebook closed")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error launching Jupyter: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print_header("Warehouse Demo - Quick Start")
    
    # Run checks
    check_python()
    check_notebook_exists()
    
    # Setup
    install_dependencies()
    
    if not check_jupyter():
        sys.exit(1)
    
    enable_ipywidgets()
    
    # Launch
    launch_jupyter()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
