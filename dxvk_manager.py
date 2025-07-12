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
        """Main installation logic."""
        try:
            # Step 1: Get latest DXVK release info
            print("Fetching latest DXVK release...")
            release_info = self.downloader.get_latest_release_info()
            version = release_info['tag_name']
            download_url = release_info['zipball_url']
            
            print(f"Latest DXVK version: {version}")
            print(f"Download URL: {download_url}")
            
            # Step 2: Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Extracting DXVK to temporary directory: {temp_dir}")
                
                # Step 3: Download and extract DXVK
                self.downloader.download_and_extract_dxvk(download_url, temp_dir, architecture, directx_version)
                
                # Step 4: Determine which DLLs to install
                dll_map = {
                    'Direct3D 9': ['d3d9.dll', 'dxgi.dll'],
                    'Direct3D 10': ['d3d10.dll', 'dxgi.dll'],
                    'Direct3D 11': ['d3d11.dll', 'dxgi.dll'],
                    'Unknown': ['d3d9.dll', 'd3d10.dll', 'd3d11.dll', 'dxgi.dll']
                }
                
                dlls_to_install = dll_map.get(directx_version, dll_map['Unknown'])
                
                # Step 5: Backup existing DLLs if requested
                if backup_enabled:
                    print("Creating backup of existing DLLs...")
                    self.file_manager.backup_dlls(game_folder, dlls_to_install)
                
                # Step 6: Copy DXVK DLLs to game folder
                print("Installing DXVK DLLs...")
                self.file_manager.copy_dlls(temp_dir, game_folder, dlls_to_install)
                
                # Step 7: Log the installation
                self.logger.log_installation(game_folder, architecture, directx_version, version)
                
                print("DXVK installation completed successfully!")
                return True
                
        except Exception as e:
            print(f"Installation failed: {str(e)}")
            return False

    def uninstall_dxvk(self, game_folder):
        """Uninstalls DXVK by restoring backups."""
        try:
            return self.file_manager.restore_dlls(game_folder)
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

