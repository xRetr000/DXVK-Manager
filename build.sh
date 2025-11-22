#!/bin/bash
# Build script for Linux - creates a standalone executable

echo "============================================================"
echo "DXVK Manager Tool - Linux Build Script"
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "dxvk_manager.py" ]; then
    echo "ERROR: dxvk_manager.py not found!"
    echo "Please run this script from the project directory."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.7 or higher."
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required dependencies..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies!"
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies found"
fi

echo ""

# Install PyInstaller if not already installed
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

echo ""

# Build executable
echo "Building DXVK Manager executable..."
python3 -m PyInstaller \
    --onefile \
    --name DXVK_Manager \
    --hidden-import pefile \
    --hidden-import requests \
    --hidden-import PyQt6 \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import platform_utils \
    --hidden-import zipfile \
    --hidden-import tarfile \
    --hidden-import io \
    --hidden-import json \
    --hidden-import datetime \
    --hidden-import tempfile \
    --hidden-import shutil \
    --clean \
    dxvk_manager.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ Build completed successfully!"
    echo ""
    echo "Your executable is ready:"
    if [ -f "dist/DXVK_Manager" ]; then
        SIZE=$(du -h dist/DXVK_Manager | cut -f1)
        echo "  dist/DXVK_Manager ($SIZE)"
    fi
    echo ""
    echo "The executable is standalone and doesn't require Python."
    echo "You can distribute it to users - they just need to run it!"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "✗ Build failed!"
    echo "Please check the error messages above."
    echo ""
    exit 1
fi

