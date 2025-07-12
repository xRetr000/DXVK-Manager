#!/usr/bin/env python3
"""
Integration test for DXVK Manager Tool
This test simulates the main workflow without actually downloading files or modifying system files.
"""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import our modules
from dxvk_manager import DXVKManager
from exe_analyzer import get_exe_architecture, detect_directx_version

def test_integration():
    """Test the complete workflow of the DXVK Manager."""
    print("Starting integration test...")
    
    # Create a temporary directory to simulate a game folder
    with tempfile.TemporaryDirectory() as temp_game_dir:
        print(f"Created temporary game directory: {temp_game_dir}")
        
        # Create a fake game executable (we'll create a minimal PE file for testing)
        fake_exe = os.path.join(temp_game_dir, "game.exe")
        
        # Create a simple file to simulate an exe (won't be a real PE file for this test)
        with open(fake_exe, "wb") as f:
            # Write minimal PE header structure for testing
            # This is a very simplified version just for testing
            f.write(b"MZ")  # DOS header signature
            f.write(b"\x00" * 58)  # Padding to PE offset
            f.write(b"\x3c\x00\x00\x00")  # PE offset (60 bytes)
            f.write(b"\x00" * 60)  # More padding
            f.write(b"PE\x00\x00")  # PE signature
            f.write(b"\x4c\x01")  # Machine type (0x014c = i386, 32-bit)
        
        # Create some DirectX DLLs to simulate detection
        d3d11_dll = os.path.join(temp_game_dir, "d3d11.dll")
        with open(d3d11_dll, "w") as f:
            f.write("fake d3d11.dll content")
        
        print("Created fake game files")
        
        # Test architecture detection
        try:
            arch = get_exe_architecture(fake_exe)
            print(f"Architecture detection result: {arch}")
        except Exception as e:
            print(f"Architecture detection failed (expected for fake PE): {e}")
            arch = "32-bit"  # Assume 32-bit for testing
        
        # Test DirectX detection
        dx_versions = detect_directx_version(temp_game_dir)
        print(f"DirectX detection result: {dx_versions}")
        
        # Test the manager with mocked download
        manager = DXVKManager()
        
        # Mock the GitHub downloader to avoid actual downloads
        with patch.object(manager.downloader, 'get_latest_release_info') as mock_release_info, \
             patch.object(manager.downloader, 'download_and_extract_dxvk') as mock_download:
            
            # Mock release info
            mock_release_info.return_value = {
                'tag_name': 'v2.3',
                'zipball_url': 'https://fake-url.com/dxvk.zip'
            }
            
            # Mock download and extract (simulate creating DLL files)
            def mock_extract(download_url, extract_path, arch, directx_version):
                # Create fake DXVK DLLs in the extract path
                fake_dlls = ['d3d11.dll', 'dxgi.dll']
                for dll in fake_dlls:
                    dll_path = os.path.join(extract_path, dll)
                    with open(dll_path, "w") as f:
                        f.write(f"fake DXVK {dll} content")
                print(f"Mocked extraction of DXVK DLLs to {extract_path}")
            
            mock_download.side_effect = mock_extract
            
            # Test installation
            print("Testing DXVK installation...")
            success = manager.install_dxvk(
                game_folder=temp_game_dir,
                architecture=arch,
                directx_version="Direct3D 11",
                backup_enabled=True
            )
            
            if success:
                print("✓ Installation test passed")
                
                # Check if backup was created
                backup_dir = os.path.join(temp_game_dir, "dxvk_backup")
                if os.path.exists(backup_dir):
                    print("✓ Backup creation test passed")
                else:
                    print("✗ Backup creation test failed")
                
                # Test uninstallation
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

