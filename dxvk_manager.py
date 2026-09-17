import os
import tempfile

from constants import get_dll_map
from file_manager import FileManager
from github_downloader import GithubDownloader, get_downloader
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
        try:
            if not game_folder or not os.path.isdir(game_folder):
                raise ValueError("Game folder does not exist: " + str(game_folder))
            if architecture not in ("32-bit", "64-bit"):
                raise ValueError("Could not determine whether the game is 32-bit or 64-bit.")
            downloader = get_downloader(source)
            self.downloader = downloader
            product = "vkd3d-proton" if source == "vkd3d-proton" else "DXVK"
            print("Fetching " + product + " release...")
            release = downloader.get_release_info(version)
            url = release.get("download_url")
            if not url:
                raise ValueError("The selected release has no downloadable archive.")
            dlls = get_dll_map(source).get(directx_version, get_dll_map(source)["Unknown"])
            with tempfile.TemporaryDirectory() as temp_dir:
                downloader.download_and_extract_dxvk(url, temp_dir, architecture, directx_version,
                                                     release.get("download_format", "tar.gz"))
                available = [d for d in dlls if os.path.isfile(os.path.join(temp_dir, d))]
                if not available:
                    raise ValueError("No required DLLs were found in the downloaded archive.")
                if backup_enabled:
                    self.file_manager.backup_dlls(game_folder, available)
                self.file_manager.copy_dlls(temp_dir, game_folder, available)
                if not all(os.path.isfile(os.path.join(game_folder, d)) for d in available):
                    raise ValueError("One or more DLLs could not be installed.")
                self.logger.log_installation(game_folder, architecture, directx_version, release["tag_name"])
                print(product + " installation completed successfully.")
                return True
        except Exception as exc:
            import traceback
            print("Installation failed: " + str(exc))
            print(traceback.format_exc())
            return False

    def uninstall_dxvk(self, game_folder):
        try:
            return self.file_manager.restore_dlls(game_folder)
        except Exception as exc:
            print("Uninstallation failed: " + str(exc))
            return False


def main():
    if DXVKManagerGUI is None:
        print("Error: GUI module not found!")
        return
    DXVKManagerGUI(DXVKManager()).run()


if __name__ == "__main__":
    main()
