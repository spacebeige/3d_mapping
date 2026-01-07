#!/bin/bash
# Quick start script for running warehouse_demo.ipynb

set -e  # Exit on error

echo "=========================================="
echo "  Warehouse Demo - Quick Start Script"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.9 or higher from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if we're in the right directory
if [ ! -f "examples/warehouse_demo.ipynb" ]; then
    echo "❌ Error: warehouse_demo.ipynb not found"
    echo "Please run this script from the repository root directory"
    exit 1
fi

echo "✓ Found warehouse_demo.ipynb"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    echo "Please install pip"
    exit 1
fi

echo "✓ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
echo ""

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo "✓ Dependencies installed from requirements.txt"
else
    echo "Installing core dependencies..."
    pip3 install numpy pandas plotly scikit-learn ipywidgets ipython pydantic networkx jupyter --quiet
    echo "✓ Core dependencies installed"
fi

# Check if jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo ""
    echo "Installing Jupyter..."
    pip3 install jupyter --quiet
fi

echo "✓ Jupyter is ready"

# Enable ipywidgets extension
echo ""
echo "🔧 Enabling ipywidgets extension..."
jupyter nbextension enable --py widgetsnbextension --sys-prefix 2>/dev/null || echo "  (extension may already be enabled)"

echo ""
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📝 Instructions:"
echo ""
echo "1. The Jupyter Notebook will open in your browser"
echo "2. Click 'Cell' → 'Run All' to run the entire notebook"
echo "3. Or use Shift+Enter to run cells one at a time"
echo "4. Interact with the widgets as they appear"
echo ""
echo "📖 For detailed instructions, see examples/README.md"
echo ""
echo "Press Enter to launch Jupyter Notebook..."
read

# Launch Jupyter
echo ""
echo "🚀 Launching Jupyter Notebook..."
echo ""
jupyter notebook examples/warehouse_demo.ipynb
