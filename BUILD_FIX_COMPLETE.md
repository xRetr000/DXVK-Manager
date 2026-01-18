# Build Executable Fix - Complete Solution

## Problem
When building the executable with `build_executable.py`, PyInstaller was missing the `gui` module, causing:
```
ModuleNotFoundError: No module named 'gui'
```

## Root Causes

1. **Import inside function**: The `from gui import DXVKManagerGUI` was inside the `main()` function, which PyInstaller might not detect reliably
2. **Missing hidden imports**: The build script didn't explicitly tell PyInstaller to include local modules
3. **Old spec file**: An outdated `DXVK_Manager.spec` file existed without the `gui` module listed

## Solutions Applied

### 1. Moved Import to Top Level ✅
**File**: `dxvk_manager.py`

Changed from:
```python
def main():
    from gui import DXVKManagerGUI  # Inside function
```

To:
```python
# At module level (top of file)
try:
    from gui import DXVKManagerGUI
except ImportError:
    DXVKManagerGUI = None
```

**Why**: PyInstaller detects top-level imports more reliably than imports inside functions.

### 2. Added All Hidden Imports ✅
**File**: `build_executable.py`

Added explicit `--hidden-import` flags for:
- `gui` - **This was the missing one!**
- `exe_analyzer`
- `file_manager`
- `logger`
- `github_downloader`
- `ctypes` (for admin detection)
- `winreg` (Windows registry)
- `traceback` (error reporting)
- `--collect-submodules PyQt6` (ensures all Qt components)

### 3. Auto-Delete Old Spec File ✅
**File**: `build_executable.py`

Added code to delete `DXVK_Manager.spec` before building so PyInstaller regenerates it with the new hidden imports.

## How to Rebuild

1. **Clean old build** (recommended):
   ```bash
   # Delete old build artifacts
   rmdir /s /q build dist
   del DXVK_Manager.spec
   ```

2. **Run build script**:
   ```bash
   python build_executable.py
   ```

3. **Test the executable**:
   ```bash
   dist\DXVK_Manager.exe
   ```

## Verification

After rebuilding, the executable should:
- ✅ Start without import errors
- ✅ Show the GUI window
- ✅ Include all local modules
- ✅ Include all PyQt6 dependencies

## Files Changed

1. **dxvk_manager.py** - Moved GUI import to top level
2. **build_executable.py** - Added hidden imports, auto-delete spec file

## If Still Having Issues

1. **Check PyInstaller version**:
   ```bash
   pip show pyinstaller
   ```
   Should be 5.0+ for best PyQt6 support

2. **Try with console enabled** (for debugging):
   Change `--noconsole` to `--console` in `build_executable.py` to see error messages

3. **Check the generated spec file**:
   After building, check `DXVK_Manager.spec` and verify `gui` is in the `hiddenimports` list

4. **Manual spec file** (if needed):
   If automatic detection still fails, you can manually edit `DXVK_Manager.spec` and add `'gui'` to the `hiddenimports` list, then run:
   ```bash
   pyinstaller DXVK_Manager.spec
   ```

## Summary

The fix ensures PyInstaller:
1. Detects the `gui` module (top-level import)
2. Includes it in the build (hidden import flag)
3. Regenerates the spec file (delete old one)

This should completely resolve the `ModuleNotFoundError: No module named 'gui'` issue.
