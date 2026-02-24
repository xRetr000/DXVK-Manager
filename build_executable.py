#!/usr/bin/env python3
"""
Build script for creating a standalone executable of the DXVK Manager Tool.
This script uses PyInstaller to package the application.

Just run: python build_executable.py
Or double-click: BUILD.bat (Windows)
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
    
    # Remove old spec file if it exists to force regeneration with new hidden imports
    spec_file = "DXVK_Manager.spec"
    if os.path.exists(spec_file):
        print(f"Removing old spec file: {spec_file}")
        try:
            os.remove(spec_file)
        except Exception as e:
            print(f"Warning: Could not remove old spec file: {e}")
    
    # PyInstaller command
    # Note: --windowed hides console, but we keep console for debugging for now
    # Change --noconsole to --windowed if you want no console window
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Create a single executable file
        "--noconsole",  # Hide console window (for GUI apps) - use --windowed for Mac
        "--name", "DXVK_Manager",
        "--hidden-import", "pefile",
        "--hidden-import", "requests",
        # PyQt6 modules
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--collect-submodules", "PyQt6",  # Collect all PyQt6 submodules
        # Local modules - must be explicitly included for PyInstaller
        "--hidden-import", "gui",
        "--hidden-import", "exe_analyzer",
        "--hidden-import", "file_manager",
        "--hidden-import", "logger",
        "--hidden-import", "github_downloader",
        # Standard library modules
        "--hidden-import", "zipfile",
        "--hidden-import", "io",
        "--hidden-import", "json",
        "--hidden-import", "datetime",
        "--hidden-import", "tempfile",
        "--hidden-import", "shutil",
        "--hidden-import", "ctypes",  # For admin detection
        "--hidden-import", "winreg",  # Windows registry access
        "--hidden-import", "traceback",  # For error reporting
        "--clean",  # Clean PyInstaller cache before building
        # Remove old spec file if it exists to force regeneration
        "dxvk_manager.py"
    ]
    
    # Add icon if it exists
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        print("Executable can be found in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print("\nTrying with console window enabled for debugging...")
        # Try again with console enabled for debugging
        cmd_console = [c for c in cmd if c != "--noconsole"]
        try:
            subprocess.check_call(cmd_console)
            print("Build completed with console window enabled!")
            print("Executable can be found in the 'dist' folder.")
        except subprocess.CalledProcessError as e2:
            print(f"Build with console also failed: {e2}")
            return False
    
    return True

def main():
    """Main build process."""
    print("=" * 60)
    print("DXVK Manager Tool - Build Script")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("dxvk_manager.py"):
        print("ERROR: dxvk_manager.py not found!")
        print("Please run this script from the project directory.")
        print()
        input("Press Enter to exit...")
        return False
    
    # Check if dependencies are installed
    print("Checking dependencies...")
    try:
        import requests
        import pefile
        print("✓ Dependencies found")
    except ImportError:
        print("Installing required dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed")
        except subprocess.CalledProcessError:
            print("ERROR: Failed to install dependencies!")
            print("Please run: pip install -r requirements.txt")
            input("Press Enter to exit...")
            return False
    
    print()
    
    # Install PyInstaller
    install_pyinstaller()
    
    print()
    
    # Build executable
    success = build_executable()
    
    print()
    print("=" * 60)
    if success:
        print("✓ Build completed successfully!")
        print()
        print("Your executable is ready:")
        exe_path = os.path.join("dist", "DXVK_Manager.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"  {exe_path} ({size_mb:.1f} MB)")
        print()
        print("The executable is standalone and doesn't require Python.")
        print("You can distribute it to users - they just need to double-click it!")
        print()
    else:
        print("✗ Build failed!")
        print("Please check the error messages above.")
        print()
    
    # Wait for user input on Windows (in case run from double-click)
    if sys.platform == "win32":
        input("Press Enter to exit...")
    
    return success

if __name__ == "__main__":
    main()

