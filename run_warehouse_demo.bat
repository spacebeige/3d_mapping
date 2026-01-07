@echo off
REM Quick start script for running warehouse_demo.ipynb on Windows

echo ==========================================
echo   Warehouse Demo - Quick Start Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check if we're in the right directory
if not exist "examples\warehouse_demo.ipynb" (
    echo Error: warehouse_demo.ipynb not found
    echo Please run this script from the repository root directory
    pause
    exit /b 1
)

echo [OK] Found warehouse_demo.ipynb

REM Install dependencies
echo.
echo Installing dependencies...
echo.

if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    echo [OK] Dependencies installed from requirements.txt
) else (
    echo Installing core dependencies...
    pip install numpy pandas plotly scikit-learn ipywidgets ipython pydantic networkx jupyter --quiet
    echo [OK] Core dependencies installed
)

REM Check if jupyter is installed
jupyter --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing Jupyter...
    pip install jupyter --quiet
)

echo [OK] Jupyter is ready

REM Enable ipywidgets extension
echo.
echo Enabling ipywidgets extension...
jupyter nbextension enable --py widgetsnbextension --sys-prefix 2>nul

echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Instructions:
echo.
echo 1. The Jupyter Notebook will open in your browser
echo 2. Click 'Cell' -^> 'Run All' to run the entire notebook
echo 3. Or use Shift+Enter to run cells one at a time
echo 4. Interact with the widgets as they appear
echo.
echo For detailed instructions, see examples\README.md
echo.
echo Press any key to launch Jupyter Notebook...
pause >nul

REM Launch Jupyter
echo.
echo Launching Jupyter Notebook...
echo.
jupyter notebook examples\warehouse_demo.ipynb
