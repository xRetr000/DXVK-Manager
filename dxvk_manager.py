import os
import tempfile
from github_downloader import GithubDownloader, get_downloader
from constants import get_dll_map
from file_manager import FileManager
from logger import Logger

try:
    from gui import DXVKManagerGUI
except ImportError:
    DXVKManagerGUI = None


class DXVKManager:
    def __init__(self):
        self.downloader = GithubDownloader()
        self.file_manager = FileManager()
        self.logger = Logger()

    def install_dxvk(self, game_folder, architecture, directx_version, backup_enabled,
                     source="official", version=None):
        """Download and install the selected DXVK or vkd3d-proton source."""
        try:
            if not game_folder or not os.path.exists(game_folder):
                raise ValueError(f"Game folder does not exist: {game_folder}")
            if architecture not in ["32-bit", "64-bit"]:
                raise ValueError("Could not detect game architecture (32-bit or 64-bit).")

            downloader = get_downloader(source)
            self.downloader = downloader
            product = "vkd3d-proton" if source == "vkd3d-proton" else "DXVK"
            print(f"Fetching {product} release from {downloader.source_name}...")
            release_info = downloader.get_release_info(version)
            resolved_version = release_info["tag_name"]
            download_url = release_info.get("download_url") or release_info.get("zipball_url")
            file_format = release_info.get("download_format", "tar.gz")
            if not download_url:
                raise ValueError("The selected release has no downloadable asset.")

            print(f"{product} version: {resolved_version}")
            print(f"Download URL: {download_url}")
            print(f"File format: {file_format}")

            dll_map = get_dll_map(source)
            dlls_to_install = dll_map.get(directx_version, dll_map["Unknown"])
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Extracting {product} to temporary directory: {temp_dir}")
                downloader.download_and_extract_dxvk(download_url, temp_dir, architecture,
                                                     directx_version, file_format)
                extracted_dlls = [dll for dll in dlls_to_install
                                  if os.path.exists(os.path.join(temp_dir, dll))]
                missing_dlls = [dll for dll in dlls_to_install if dll not in extracted_dlls]
                if not extracted_dlls:
                    raise ValueError(f"Failed to extract required DLLs: {', '.join(missing_dlls)}")
                if missing_dlls:
                    print(f"Warning: Missing DLLs: {', '.join(missing_dlls)}")
                    dlls_to_install = extracted_dlls

                if backup_enabled:
                    print("Creating backup of existing DLLs...")
                    self.file_manager.backup_dlls(game_folder, dlls_to_install)
                print(f"Installing {product} DLLs...")
                self.file_manager.copy_dlls(temp_dir, game_folder, dlls_to_install)
                installed_dlls = [dll for dll in dlls_to_install
                                  if os.path.exists(os.path.join(game_folder, dll))]
                if not installed_dlls:
                    raise ValueError("No DLLs were installed. Check permissions and close the game.")
                self.logger.log_installation(game_folder, architecture, directx_version, resolved_version)
                print(f"{product} installation completed successfully! Installed: {', '.join(installed_dlls)}")
                return True
        except Exception as exc:
            print(f"Installation failed: {exc}")
            import traceback
            print(f"Error details: {traceback.format_exc()}")
            return False

    def uninstall_dxvk(self, game_folder):
        try:
            return self.file_manager.restore_dlls(game_folder)
        except Exception as exc:
            print(f"Uninstallation failed: {exc}")
            return False


def _add_vkd3d_to_gui(gui):
    """Add vkd3d-proton controls to the current GUI without breaking older layouts."""
    source_combo = getattr(gui, "source_combo", None)
    if source_combo is not None and source_combo.findData("vkd3d-proton") < 0:
        source_combo.addItem("vkd3d-proton (HansKristian-Work)", "vkd3d-proton")
    directx_combo = getattr(gui, "directx_combo", None)
    if directx_combo is not None and directx_combo.findText("Direct3D 12") < 0:
        directx_combo.addItem("Direct3D 12")


def main():
    if DXVKManagerGUI is None:
        print("Error: GUI module not found!")
        return
    manager = DXVKManager()
    gui = DXVKManagerGUI(manager)
    _add_vkd3d_to_gui(gui)
    gui.run()


if __name__ == "__main__":
    main()
