#!/usr/bin/env python3
"""
Build script for creating a standalone executable of the DXVK Manager Tool.
This script uses PyInstaller to package the application.
"""

import os
import subprocess
import sys

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Build the standalone executable."""
    print("Building DXVK Manager executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window (for GUI apps)
        "--name", "DXVK_Manager",
        "--icon", "icon.ico" if os.path.exists("icon.ico") else None,
        "dxvk_manager.py"
    ]
    
    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        print("Executable can be found in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

def main():
    """Main build process."""
    print("DXVK Manager Tool - Build Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("dxvk_manager.py"):
        print("Error: dxvk_manager.py not found. Please run this script from the project directory.")
        return
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    success = build_executable()
    
    if success:
        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist' folder.")
        print("The executable is standalone and doesn't require Python to be installed.")
    else:
        print("\nBuild failed. Please check the error messages above.")

if __name__ == "__main__":
    main()

