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
        self.selected_source = "official"

    def install_dxvk(self, game_folder, architecture, directx_version, backup_enabled,
                     source=None, version=None):
        """Download and install the selected DXVK or vkd3d-proton source."""
        try:
            if not game_folder or not os.path.isdir(game_folder):
                raise ValueError("Game folder does not exist: " + str(game_folder))
            if architecture not in ("32-bit", "64-bit"):
                raise ValueError("Could not determine whether the game is 32-bit or 64-bit.")

            source = source or self.selected_source or "official"
            # Reuse the default downloader when no source/version was explicitly
            # selected. This preserves compatibility with existing tests/mocks.
            if source == "official" and version is None and isinstance(self.downloader, GithubDownloader):
                downloader = self.downloader
            else:
                downloader = get_downloader(source)
                self.downloader = downloader

            product = "vkd3d-proton" if source == "vkd3d-proton" else "DXVK"
            print("Fetching " + product + " release...")
            release = downloader.get_release_info(version)
            url = release.get("download_url")
            if not url:
                raise ValueError("The selected release has no downloadable archive.")

            dll_map = get_dll_map(source)
            dlls = dll_map.get(directx_version, dll_map["Unknown"])
            with tempfile.TemporaryDirectory() as temp_dir:
                downloader.download_and_extract_dxvk(
                    url,
                    temp_dir,
                    architecture,
                    directx_version,
                    release.get("download_format", "tar.gz"),
                )
                available = [d for d in dlls if os.path.isfile(os.path.join(temp_dir, d))]
                if not available:
                    raise ValueError("No required DLLs were found in the downloaded archive.")
                if backup_enabled:
                    self.file_manager.backup_dlls(game_folder, available)
                self.file_manager.copy_dlls(temp_dir, game_folder, available)
                if not all(os.path.isfile(os.path.join(game_folder, d)) for d in available):
                    raise ValueError("One or more DLLs could not be installed.")
                self.logger.log_installation(
                    game_folder, architecture, directx_version, release["tag_name"]
                )
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


def _configure_gui(gui, manager):
    """Add source controls to the existing GUI without duplicating its layout."""
    from PyQt6.QtWidgets import QLabel, QComboBox

    directx_combo = getattr(gui, "directx_combo", None)
    if directx_combo is None:
        return

    parent_layout = directx_combo.parentWidget().layout()
    if parent_layout is None:
        return

    source_label = QLabel("3. Graphics Source")
    source_combo = QComboBox()
    source_combo.addItem("Official DXVK (doitsujin)", "official")
    source_combo.addItem("DXVK GPLAsync (Ph42oN)", "gplasync")
    source_combo.addItem("vkd3d-proton (HansKristian-Work)", "vkd3d-proton")
    source_combo.setToolTip("Choose the graphics translation layer to install")

    def source_changed(index):
        source = source_combo.itemData(index)
        manager.selected_source = source
        d3d12_index = directx_combo.findText("Direct3D 12")
        if source == "vkd3d-proton":
            if d3d12_index < 0:
                directx_combo.addItem("Direct3D 12")
            directx_combo.setCurrentText("Direct3D 12")
            gui.install_btn.setText("4. Install vkd3d-proton")
            gui.install_btn.setToolTip("Downloads and installs vkd3d-proton DLLs")
        else:
            if directx_combo.currentText() == "Direct3D 12":
                directx_combo.setCurrentText("Auto-detect")
            gui.install_btn.setText("4. Install DXVK")
            gui.install_btn.setToolTip("Downloads and installs DXVK DLLs")

    source_combo.currentIndexChanged.connect(source_changed)
    parent_layout.insertWidget(parent_layout.indexOf(directx_combo), source_label)
    parent_layout.insertWidget(parent_layout.indexOf(directx_combo), source_combo)
    gui.source_combo = source_combo


def main():
    if DXVKManagerGUI is None:
        print("Error: GUI module not found!")
        return
    manager = DXVKManager()
    gui = DXVKManagerGUI(manager)
    _configure_gui(gui, manager)
    gui.run()


if __name__ == "__main__":
    main()
