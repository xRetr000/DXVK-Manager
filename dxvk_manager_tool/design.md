
This document outlines the design and architecture of the DXVK Manager Tool.

## 1. Application Structure

The application will be composed of the following modules:

- **`dxvk_manager.py`**: The main application logic, responsible for coordinating the other modules.
- **`gui.py`**: The user interface, built with Tkinter.
- **`exe_analyzer.py`**: Analyzes executable files to determine architecture and DirectX version.
- **`github_downloader.py`**: Downloads and extracts DXVK releases from GitHub.
- **`file_manager.py`**: Handles file operations like copying, backing up, and creating symlinks.
- **`logger.py`**: Logs application activity to a JSON file.

## 2. Module Responsibilities

### `dxvk_manager.py`

- Initializes the GUI.
- Handles user requests from the GUI.
- Calls the appropriate utility modules to perform tasks.
- Manages the overall state of the application.

### `gui.py`

- Creates the main application window.
- Defines and lays out all UI elements (buttons, labels, etc.).
- Binds UI events to functions in `dxvk_manager.py`.
- Displays status messages and logs to the user.

### `exe_analyzer.py`

- Reads the PE header of an `.exe` file to determine if it's 32-bit or 64-bit.
- Scans a directory for DirectX-related DLLs (`d3d9.dll`, `d3d10.dll`, `d3d11.dll`) to infer the DirectX version.

### `github_downloader.py`

- Uses the GitHub API to find the latest DXVK release.
- Downloads the release ZIP file.
- Extracts the required DLLs from the ZIP archive.

### `file_manager.py`

- Copies files from the extracted DXVK release to the game directory.
- Creates backups of existing DLLs before overwriting them.
- (Optional) Creates symbolic links instead of copying files.

### `logger.py`

- Records installation events to `dxvk_manager_log.json`.
- Each log entry will include the game path, architecture, DirectX version, DXVK version, and a timestamp.

## 3. UI Layout

The UI will have the following components:

- A "Select Game Folder" button to open a file dialog.
- A label to display the selected game folder path.
- A display area for the auto-detected architecture and DirectX version.
- A dropdown menu to manually override the DirectX version.
- A checkbox to enable or disable backing up existing DLLs.
- An "Install DXVK" button to start the installation process.
- A text area to show status messages and logs.


