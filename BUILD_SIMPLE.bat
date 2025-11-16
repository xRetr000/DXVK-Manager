@echo off
REM Ultra-simple build script - just double-click and wait!
title DXVK Manager - Building...

echo Building DXVK Manager executable...
echo This may take a few minutes, please wait...
echo.

python build_executable.py

if errorlevel 1 (
    echo.
    echo Build failed! Make sure Python is installed.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo Done! Check the 'dist' folder for DXVK_Manager.exe
    timeout /t 3 >nul
)

