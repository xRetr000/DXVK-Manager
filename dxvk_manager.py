import os
import tempfile
from github_downloader import GithubDownloader
from file_manager import FileManager
from logger import Logger

class DXVKManager:
    def __init__(self):
        self.downloader = GithubDownloader()
        self.file_manager = FileManager()
        self.logger = Logger()

    def install_dxvk(self, game_folder, architecture, directx_version, backup_enabled):
        """Main installation logic with Windows-specific error handling."""
        try:
            # Validate inputs with user-friendly messages
            if not game_folder or not os.path.exists(game_folder):
                raise ValueError(
                    f"Game folder does not exist:\n{game_folder}\n\n"
                    "Please select a valid game folder containing the game's .exe file."
                )
            
            if architecture not in ["32-bit", "64-bit"]:
                if architecture in ["Not detected", "Unknown", "Error"]:
                    raise ValueError(
                        "Could not detect game architecture.\n\n"
                        "Please ensure:\n"
                        "1. The folder contains a valid .exe file\n"
                        "2. The .exe file is not corrupted\n"
                        "3. You have read permissions for the folder"
                    )
                else:
                    raise ValueError(f"Invalid architecture: {architecture}")
            
            # Step 1: Get latest DXVK release info
            print("Fetching latest DXVK release...")
            release_info = self.downloader.get_latest_release_info()
            version = release_info['tag_name']
            download_url = release_info.get('download_url') or release_info.get('zipball_url')
            file_format = release_info.get('download_format', 'tar.gz')
            
            if not download_url:
                raise ValueError(
                    "Could not find DXVK download URL.\n\n"
                    "Possible causes:\n"
                    "- No internet connection\n"
                    "- GitHub API is unavailable\n"
                    "- DXVK release format changed\n\n"
                    "Please check your internet connection and try again."
                )
            
            print(f"Latest DXVK version: {version}")
            print(f"Download URL: {download_url}")
            print(f"File format: {file_format}")
            
            # Step 2: Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Extracting DXVK to temporary directory: {temp_dir}")
                
                # Step 3: Download and extract DXVK
                self.downloader.download_and_extract_dxvk(download_url, temp_dir, architecture, directx_version, file_format)
                
                # Step 4: Determine which DLLs to install
                # Note: DXVK doesn't include d3d10.dll (it uses d3d10core.dll for D3D10.1 support)
                dll_map = {
                    'Direct3D 9': ['d3d9.dll', 'dxgi.dll'],
                    'Direct3D 10': ['d3d10core.dll', 'dxgi.dll'],  # DXVK uses d3d10core.dll, not d3d10.dll
                    'Direct3D 11': ['d3d11.dll', 'dxgi.dll'],
                    'Unknown': ['d3d9.dll', 'd3d11.dll', 'dxgi.dll']  # Don't include d3d10.dll as it doesn't exist in DXVK
                }
                
                dlls_to_install = dll_map.get(directx_version, dll_map['Unknown'])
                
                # Verify DLLs were extracted - only check for DLLs that actually exist
                missing_dlls = []
                extracted_dlls = []
                for dll in dlls_to_install:
                    dll_path = os.path.join(temp_dir, dll)
                    if os.path.exists(dll_path):
                        extracted_dlls.append(dll)
                    else:
                        missing_dlls.append(dll)
                
                # If we have at least some DLLs extracted, proceed (especially for Unknown case)
                if not extracted_dlls:
                    raise ValueError(
                        f"Failed to extract required DLLs.\n\n"
                        f"Missing DLLs: {', '.join(missing_dlls)}\n\n"
                        "Possible causes:\n"
                        "- DXVK release structure changed\n"
                        "- Architecture mismatch\n"
                        "- Download was corrupted\n\n"
                        "Please try again or report this issue."
                    )
                
                # Warn about missing DLLs but don't fail if we have some
                if missing_dlls:
                    print(f"Warning: Some DLLs were not found: {', '.join(missing_dlls)}. Continuing with available DLLs: {', '.join(extracted_dlls)}")
                    # Update dlls_to_install to only include what we actually have
                    dlls_to_install = extracted_dlls
                
                # Step 5: Backup existing DLLs if requested
                if backup_enabled:
                    print("Creating backup of existing DLLs...")
                    self.file_manager.backup_dlls(game_folder, dlls_to_install)
                
                # Step 6: Copy DXVK DLLs to game folder
                print("Installing DXVK DLLs...")
                self.file_manager.copy_dlls(temp_dir, game_folder, dlls_to_install)
                
                # Verify installation
                installed_dlls = []
                for dll in dlls_to_install:
                    dll_path = os.path.join(game_folder, dll)
                    if os.path.exists(dll_path):
                        installed_dlls.append(dll)
                    else:
                        print(f"Warning: {dll} was not installed successfully.")
                
                if not installed_dlls:
                    raise ValueError(
                        "No DLLs were installed.\n\n"
                        "Possible causes:\n"
                        "- Insufficient permissions (try running as administrator)\n"
                        "- Game folder is read-only\n"
                        "- Files are locked by another program\n"
                        "- Antivirus is blocking the operation\n\n"
                        "If the game is in Program Files, you may need to:\n"
                        "1. Run DXVK Manager as administrator, OR\n"
                        "2. Move the game to a folder outside Program Files"
                    )
                
                # Step 7: Log the installation
                self.logger.log_installation(game_folder, architecture, directx_version, version)
                
                print(f"DXVK installation completed successfully! Installed: {', '.join(installed_dlls)}")
                return True
                
        except PermissionError as e:
            # Permission errors already have user-friendly messages
            print(f"Installation failed: {str(e)}")
            return False
        except ValueError as e:
            # Validation errors already have user-friendly messages
            print(f"Installation failed: {str(e)}")
            return False
        except Exception as e:
            error_msg = (
                f"Installation failed with unexpected error:\n{str(e)}\n\n"
                "Please check:\n"
                "- Internet connection\n"
                "- Game folder permissions\n"
                "- Antivirus settings\n"
                "- Windows Event Viewer for more details"
            )
            print(error_msg)
            import traceback
            print(f"\nTechnical details:\n{traceback.format_exc()}")
            return False

    def uninstall_dxvk(self, game_folder):
        """Uninstalls DXVK by restoring backups."""
        try:
            if not game_folder or not os.path.exists(game_folder):
                print("Error: Game folder does not exist.")
                return False
            return self.file_manager.restore_dlls(game_folder)
        except PermissionError as e:
            print(f"Uninstallation failed: {str(e)}")
            return False
        except Exception as e:
            print(f"Uninstallation failed: {str(e)}")
            return False

def main():
    """Main entry point for the application."""
    manager = DXVKManager()
    
    # Import GUI here to avoid circular imports
    from gui import DXVKManagerGUI
    
    # Create and run the GUI
    gui = DXVKManagerGUI(manager)
    gui.run()

if __name__ == "__main__":
    main()

