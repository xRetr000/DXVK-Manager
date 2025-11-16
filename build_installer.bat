@echo off
REM Build both executable and installer in one go!
title DXVK Manager - Building Installer Package

echo ========================================
echo DXVK Manager - Build Installer
echo ========================================
echo.

REM Step 1: Build executable
echo [Step 1/2] Building executable...
call BUILD.bat
if errorlevel 1 (
    echo.
    echo Failed to build executable. Cannot create installer.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [Step 2/2] Creating Installer
echo ========================================
echo.

REM Check if Inno Setup is available
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if exist %INNO_PATH% (
    echo Found Inno Setup!
    echo.
    
    if not exist "installer.iss" (
        echo Creating installer.iss template...
        echo See INSTALLER_GUIDE.md for instructions on creating installer.iss
        echo.
    ) else (
        echo Compiling installer with Inno Setup...
        %INNO_PATH% installer.iss
        if errorlevel 1 (
            echo.
            echo Installer compilation failed!
            pause
            exit /b 1
        )
        echo.
        echo ========================================
        echo Installer created successfully!
        echo Check the 'installer_output' folder.
        echo ========================================
        echo.
    )
) else (
    echo Inno Setup not found.
    echo.
    echo To create an installer:
    echo 1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo 2. Create installer.iss (see INSTALLER_GUIDE.md)
    echo 3. Run this script again
    echo.
    echo For now, you can distribute DXVK_Manager.exe directly.
    echo.
)

echo Done! Your executable is ready in the 'dist' folder.
echo.
pause

