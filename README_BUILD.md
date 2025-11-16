# Building DXVK Manager for Distribution

## 🚀 Easy Way (No Terminal Needed!)

### For Windows Users:

1. **Double-click `BUILD.bat`**
   - That's it! The script will:
     - Check if Python is installed
     - Install required dependencies
     - Build the executable automatically
   - When done, your executable will be in the `dist` folder

2. **Or use the simple version:**
   - Double-click `BUILD_SIMPLE.bat` for a minimal build process

## 📦 What You Get

After building, you'll find:
- **`dist/DXVK_Manager.exe`** - The standalone executable (20-50 MB)
- This file can be distributed to anyone
- Users don't need Python installed - just double-click and run!

## 🔧 Requirements for Building

- **Windows 10/11**
- **Python 3.7+** installed (download from [python.org](https://www.python.org))
  - ⚠️ **Important**: Check "Add Python to PATH" during installation!

## 📤 Distribution Options

### Option 1: Direct Distribution
- Zip the `DXVK_Manager.exe` file
- Share it with users
- They can extract and run it directly

### Option 2: Installer Package (Recommended for Store)
See `INSTALLER_GUIDE.md` for creating a professional installer.

### Option 3: Microsoft Store
The app can be packaged for Microsoft Store. See `STORE_GUIDE.md` for details.

## 🎯 Quick Start

1. Download the source code
2. Double-click `BUILD.bat`
3. Wait for build to complete (2-5 minutes)
4. Find `DXVK_Manager.exe` in the `dist` folder
5. Test it by double-clicking the .exe
6. Distribute the .exe file!

## ⚠️ Troubleshooting

### "Python is not recognized"
- Install Python from python.org
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after installing

### "Build failed"
- Make sure you're connected to the internet (needs to download dependencies)
- Try running as Administrator
- Check that all files from the repository are present

### "Module not found" errors
- Run `pip install -r requirements.txt` manually
- Make sure you're in the project directory

## 💡 Tips

- **First build takes longer** - It downloads PyInstaller and dependencies
- **Executable size**: 20-50 MB is normal (includes Python runtime)
- **Antivirus warnings**: Some antivirus may flag PyInstaller executables (false positive)
- **Test before distributing**: Always test the .exe on a clean system

## 🎁 Ready for Users

Once built, the executable is completely standalone:
- ✅ No Python required
- ✅ No installation needed
- ✅ Just double-click and run
- ✅ Works on any Windows 10/11 PC

