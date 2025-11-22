# DXVK Manager Tool

A modern Windows application for automatically installing and managing DXVK files for your games. DXVK is a Vulkan-based translation layer for Direct3D 9, 10, and 11 that can improve performance and compatibility for many games.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 🚀 Quick Start

**Just download `DXVK_Manager.exe` and double-click it!** No installation needed.

**Want to build it yourself?** Just double-click `BUILD.bat` - no terminal needed!

See `QUICK_START.md` for detailed instructions.

## Features

🔧 **Core Features:**
- **Modern Dark Mode UI** - Beautiful PyQt6-based interface with Windows 11-inspired design
- Browse and select game folders with an intuitive GUI
- Automatic detection of game architecture (32-bit or 64-bit) by analyzing PE headers
- Smart DirectX version detection (Direct3D 9, 10, or 11) by scanning for existing DLLs
- Automatic download of the latest DXVK release from GitHub (supports both .zip and .tar.gz formats)
- Intelligent installation of the correct DXVK DLLs based on game requirements

🧠 **Advanced Features:**
- Automatic backup of existing DLLs before installation
- Complete installation logging with JSON-based activity records
- Real-time activity log with detailed error messages and tracebacks
- Easy uninstallation with automatic backup restoration
- Manual DirectX version override for edge cases
- Progress tracking and detailed status messages
- Thread-safe operations for smooth UI experience

## Requirements

- **Operating System:** Windows 10 or Windows 11
- **Python:** 3.7 or higher (for running from source)
- **Dependencies:** See `requirements.txt`
  - PyQt6 (GUI framework)
  - pefile (PE file analysis)
  - requests (HTTP requests for GitHub API)

## Installation

### For End Users (Download and Run)

**Just download `DXVK_Manager.exe` and double-click it!**  
No installation, no Python, no dependencies needed.

### For Developers (Build from Source)

#### Option 1: Run from Source

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python dxvk_manager.py
   ```

### Option 2: Standalone Executable (No Terminal Required!)

**Super Easy Build - Just Double-Click!**

1. **Double-click `BUILD.bat`** (Windows)
   - That's it! It will automatically:
     - Check Python installation
     - Install dependencies
     - Build the executable
   - No terminal/command line knowledge needed!

2. **Find your executable:**
   - Location: `dist/DXVK_Manager.exe`
   - Size: ~20-50 MB (includes everything needed)
   - Standalone: No Python or dependencies required!

3. **Distribute it:**
   - Share the `.exe` file with anyone
   - They can just double-click and run it
   - Perfect for Windows Store distribution too!

**For detailed instructions, see `README_BUILD.md`**

**Want to create a professional installer?** See `INSTALLER_GUIDE.md`

## Usage

### Basic Installation Process

1. **Launch the Application**
   - Run `python dxvk_manager.py` or use the executable

2. **Select Game Folder**
   - Click "Browse" to select your game's installation folder
   - The folder should contain the main game executable (.exe file)

3. **Review Auto-Detection**
   - The tool will automatically detect:
     - Game architecture (32-bit or 64-bit)
     - DirectX version used by the game
   - If detection fails, you can manually override the DirectX version

4. **Configure Options**
   - **Backup existing DLLs:** Recommended to keep checked for safety
   - **DirectX Override:** Use if auto-detection is incorrect

5. **Install DXVK**
   - Click "Install DXVK" to begin the process
   - Monitor progress in the status area
   - Installation typically takes 30-60 seconds

6. **Launch Your Game**
   - Start your game normally
   - DXVK should now be active (you may see improved performance)

### Uninstalling DXVK

1. Select the same game folder where DXVK was installed
2. Click "Uninstall DXVK"
3. The tool will restore the original DLL files from backup

## How It Works

### Architecture Detection
The tool analyzes the PE (Portable Executable) header of your game's main .exe file to determine if it's 32-bit or 64-bit. This ensures the correct DXVK binaries are installed.

### DirectX Version Detection
The application scans the game folder for existing DirectX DLLs:
- `d3d9.dll` → Direct3D 9
- `d3d10.dll` or `d3d10core.dll` → Direct3D 10/10.1
- `d3d11.dll` → Direct3D 11

**Note:** If DirectX version cannot be detected automatically, you can manually override it using the dropdown menu.

### DXVK Installation
1. Fetches the latest DXVK release information from GitHub API
2. Downloads the release archive (.tar.gz or .zip format)
3. Extracts only the required DLLs (x32 or x64) based on your game's architecture
4. Backs up any existing DirectX DLLs in your game folder (if enabled)
5. Copies the DXVK DLLs to your game folder
6. Verifies the installation was successful
7. Logs the installation details for future reference

**Note:** DXVK releases are downloaded on-demand from GitHub. The application does not bundle DXVK files, ensuring you always get the latest version.

## File Structure

```
dxvk_manager/
├── dxvk_manager.py      # Main application entry point and core logic
├── gui.py               # PyQt6-based modern dark mode user interface
├── exe_analyzer.py      # PE header analysis and DirectX detection
├── github_downloader.py # DXVK download and extraction (supports .zip and .tar.gz)
├── file_manager.py      # File operations (copy, backup, restore)
├── logger.py            # Installation activity logging (JSON format)
├── requirements.txt     # Python dependencies
├── build_executable.py  # PyInstaller build script
├── test_modules.py      # Unit tests
├── test_integration.py  # Integration tests
└── README.md           # This documentation
```

## Logging

All DXVK installations are logged to `dxvk_manager_log.json` in the application directory. Each log entry includes:
- Timestamp of installation
- Game folder path
- Detected architecture
- DirectX version
- DXVK version installed

Example log entry:
```json
{
  "timestamp": "2024-01-15T14:30:45.123456",
  "game_path": "C:\\Games\\MyGame",
  "architecture": "64-bit",
  "directx_version": "Direct3D 11",
  "dxvk_version": "v2.3"
}
```

## Troubleshooting

### Common Issues

**"No .exe files found in the selected folder"**
- Ensure you've selected the correct game installation folder
- The folder should contain the main game executable
- Some games may have their .exe files in subfolders

**"Not a valid PE file" error**
- The selected .exe file may be corrupted or not a standard Windows executable
- Try selecting a different .exe file if multiple exist
- Some game launchers are not the actual game executable

**"Architecture detection failed"**
- Manually verify if your game is 32-bit or 64-bit
- Check the game's system requirements or documentation
- 64-bit games are more common on modern systems

**Installation fails during download**
- Check your internet connection
- Ensure Windows Defender or antivirus isn't blocking the download
- Check the activity log for detailed error messages
- The application supports both .zip and .tar.gz formats - if one fails, the other will be tried
- Try running the application as administrator

**Game doesn't start after DXVK installation**
- Use the "Uninstall DXVK" feature to restore original files
- Some games may not be compatible with DXVK
- Check game-specific compatibility lists online

### Advanced Troubleshooting

**Multiple .exe files detected**
- The tool will use the first .exe file found
- If this is incorrect, manually verify which is the main game executable
- Some games have separate launcher and game executables

**DirectX version detection is wrong or shows "Not detected"**
- Use the "Override DirectX" dropdown to manually select the correct version
- When in doubt, try "Direct3D 11" first as it's most common for modern games
- Older games (pre-2008) typically use Direct3D 9
- If detection fails, the app will install all available DLLs (d3d9.dll, d3d11.dll, dxgi.dll) when set to "Unknown"

**Backup restoration fails**
- Ensure the game is not running during uninstallation
- Check that you have write permissions to the game folder
- Some games may require administrator privileges

## Performance Tips

- DXVK typically provides the most benefit for older DirectX 9 and 10 games
- Modern DirectX 11 games may see smaller improvements
- Performance gains vary significantly between different games and hardware
- Monitor your game's frame rate before and after installation to measure impact

## Safety Notes

- Always keep the "Backup existing DLLs" option enabled
- Test games after DXVK installation to ensure compatibility
- Keep the original game installation files as an additional backup
- Some antivirus software may flag DXVK DLLs as suspicious (false positive)

## Contributing

This project is open source. Contributions are welcome for:
- Bug fixes and improvements
- Additional DirectX version detection methods
- Enhanced error handling
- UI/UX improvements
- Documentation updates

## License

This tool is provided as-is for educational and personal use. DXVK itself is licensed under the zlib/libpng license. Please respect the licenses of all components.

## Credits

- **DXVK Project:** https://github.com/doitsujin/dxvk
- **PE File Analysis:** [pefile](https://github.com/erocarrera/pefile) library
- **GUI Framework:** [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - Modern Qt6 bindings for Python
- **Build Tool:** [PyInstaller](https://www.pyinstaller.org/) for creating standalone executables

## Technology Stack

- **Language:** Python 3.7+
- **GUI:** PyQt6 (Qt6 framework)
- **Architecture:** Modular design with separate concerns
- **Threading:** QThread for non-blocking operations
- **File Formats:** Supports .zip and .tar.gz DXVK releases

---

**Disclaimer:** This tool modifies game files. While it creates backups, always ensure you have your own backups of important game installations. Use at your own risk.

