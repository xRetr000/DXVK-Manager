@echo off
REM DXVK Manager - Easy Build Script for Windows
REM Just double-click this file to build the executable!

echo ========================================
echo DXVK Manager - Building Executable
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.7 or higher from python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version
echo.

echo [2/3] Installing/updating dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo [3/3] Building executable (this may take a few minutes)...
python build_executable.py
if errorlevel 1 (
    echo.
    echo ERROR: Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is ready:
echo   dist\DXVK_Manager.exe
echo.
echo You can now distribute this .exe file to users.
echo They don't need Python installed to run it!
echo.
echo Press any key to open the dist folder...
pause >nul
if exist "dist\DXVK_Manager.exe" (
    explorer dist
) else (
    echo WARNING: Executable not found in dist folder!
)

