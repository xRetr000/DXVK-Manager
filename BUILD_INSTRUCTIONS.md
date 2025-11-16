# Building the DXVK Manager Executable

This guide explains how to build a standalone executable that users can run without installing Python.

## Prerequisites

1. **Python 3.7 or higher** installed on your system
2. All dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Build

1. Open a terminal/command prompt in the project directory
2. Run the build script:
   ```bash
   python build_executable.py
   ```

The script will:
- Automatically install PyInstaller if needed
- Build a standalone executable
- Place it in the `dist` folder

## Building Manually

If you prefer to build manually:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --noconsole --name DXVK_Manager --hidden-import pefile --hidden-import requests --hidden-import tkinter --clean dxvk_manager.py
```

## Build Options

### With Console Window (for debugging)
Remove `--noconsole` from the command to see console output:
```bash
pyinstaller --onefile --name DXVK_Manager ... dxvk_manager.py
```

### With Custom Icon
If you have an `icon.ico` file in the project directory, it will be automatically included. To use a different icon:
```bash
pyinstaller ... --icon path/to/your/icon.ico dxvk_manager.py
```

## Output

After building, you'll find:
- **Executable**: `dist/DXVK_Manager.exe` (or `dist/DXVK_Manager` on Mac/Linux)
- **Build files**: `build/` folder (can be deleted)
- **Spec file**: `DXVK_Manager.spec` (PyInstaller config, can be customized)

## Testing the Executable

1. Navigate to the `dist` folder
2. Run `DXVK_Manager.exe` (double-click or run from command line)
3. Test with a game folder that contains an .exe file

## Troubleshooting

### "Module not found" errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that `--hidden-import` flags include all required modules

### Executable is too large
- The executable includes Python interpreter and all dependencies
- This is normal for standalone executables (typically 20-50 MB)
- Consider using `--onedir` instead of `--onefile` for smaller size (but multiple files)

### Antivirus warnings
- Some antivirus software may flag PyInstaller executables as suspicious
- This is a false positive
- You may need to add an exception or submit the file for analysis

### GUI doesn't appear
- Try building without `--noconsole` to see error messages
- Check that tkinter is properly installed: `python -m tkinter`

## Distribution

The executable in the `dist` folder is standalone and can be:
- Distributed to users
- Run on Windows without Python installed
- Zipped and shared

**Note**: The executable is built for your current OS/architecture. To build for other platforms, use that platform's Python and PyInstaller.

