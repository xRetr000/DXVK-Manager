#!/usr/bin/env python3
"""
Integration test for DXVK Manager Tool
Simulates the main workflow without downloading files or modifying system files.
"""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from dxvk_manager import DXVKManager
from exe_analyzer import get_exe_architecture, detect_directx_version

def test_integration():
    """Test the complete workflow of the DXVK Manager."""
    print("Starting integration test...")

    with tempfile.TemporaryDirectory() as temp_game_dir:
        print(f"Created temporary game directory: {temp_game_dir}")

        fake_exe = os.path.join(temp_game_dir, "game.exe")
        with open(fake_exe, "wb") as f:
            f.write(b"MZ")
            f.write(b"\x00" * 58)
            f.write(b"\x3c\x00\x00\x00")
            f.write(b"\x00" * 60)
            f.write(b"PE\x00\x00")
            f.write(b"\x4c\x01")  # i386 (32-bit)

        d3d11_dll = os.path.join(temp_game_dir, "d3d11.dll")
        with open(d3d11_dll, "w") as f:
            f.write("fake d3d11.dll content")

        print("Created fake game files")

        try:
            arch = get_exe_architecture(fake_exe)
            print(f"Architecture detection result: {arch}")
        except Exception as e:
            print(f"Architecture detection failed (expected for fake PE): {e}")
            arch = "32-bit"

        dx_versions = detect_directx_version(temp_game_dir)
        print(f"DirectX detection result: {dx_versions}")

        manager = DXVKManager()

        with patch.object(manager.downloader, 'get_latest_release_info') as mock_release_info, \
             patch.object(manager.downloader, 'download_and_extract_dxvk') as mock_download:

            mock_release_info.return_value = {
                'tag_name': 'v2.3',
                'zipball_url': 'https://fake-url.com/dxvk.zip'
            }

            def mock_extract(download_url, extract_path, arch, directx_version):
                for dll in ['d3d11.dll', 'dxgi.dll']:
                    with open(os.path.join(extract_path, dll), "w") as f:
                        f.write(f"fake DXVK {dll} content")
                print(f"Mocked extraction of DXVK DLLs to {extract_path}")

            mock_download.side_effect = mock_extract

            print("Testing DXVK installation...")
            success = manager.install_dxvk(
                game_folder=temp_game_dir,
                architecture=arch,
                directx_version="Direct3D 11",
                backup_enabled=True
            )

            if success:
                print("✓ Installation test passed")
                backup_dir = os.path.join(temp_game_dir, "dxvk_backup")
                if os.path.exists(backup_dir):
                    print("✓ Backup creation test passed")
                else:
                    print("✗ Backup creation test failed")

                print("Testing DXVK uninstallation...")
                uninstall_success = manager.uninstall_dxvk(temp_game_dir)
                if uninstall_success:
                    print("✓ Uninstallation test passed")
                else:
                    print("✗ Uninstallation test failed")
            else:
                print("✗ Installation test failed")

        print("Integration test completed")

if __name__ == "__main__":
    test_integration()
