# Build Executable Fix

## Issue
When building the executable with `build_executable.py`, PyInstaller was missing the `gui` module and other local modules, causing `ModuleNotFoundError: No module named 'gui'`.

## Solution
Added explicit `--hidden-import` flags for all local modules that PyInstaller needs to include:

- `gui` - The GUI module (was missing!)
- `exe_analyzer` - Executable analysis
- `file_manager` - File operations
- `logger` - Logging functionality
- `github_downloader` - GitHub API client

Also added:
- `--collect-submodules PyQt6` - Ensures all PyQt6 components are included
- `ctypes` - Used for admin detection
- `winreg` - Windows registry access
- `traceback` - Error reporting

## Changes Made
Updated `build_executable.py` to include all necessary hidden imports.

## Testing
After rebuilding with `python build_executable.py`, the executable should now:
1. Include all local modules
2. Include all PyQt6 dependencies
3. Include Windows-specific modules (ctypes, winreg)
4. Run without import errors

## Rebuild Instructions
1. Delete the `build/` and `dist/` folders (optional, but recommended)
2. Run: `python build_executable.py`
3. Test the executable: `dist/DXVK_Manager.exe`
