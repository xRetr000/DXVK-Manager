import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Import our modules
from logger import Logger
from file_manager import FileManager

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_log.json")
        self.logger = Logger(self.log_file)

    def test_log_installation(self):
        """Test logging an installation event."""
        self.logger.log_installation(
            game_path="/path/to/game",
            architecture="64-bit",
            directx_version="Direct3D 11",
            dxvk_version="2.3"
        )
        
        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["game_path"], "/path/to/game")
        self.assertEqual(logs[0]["architecture"], "64-bit")

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager()

    def test_backup_dlls(self):
        """Test backing up DLL files."""
        # Create a test DLL file
        test_dll = os.path.join(self.temp_dir, "d3d11.dll")
        with open(test_dll, "w") as f:
            f.write("test content")
        
        # Backup the DLL
        backed_up = self.file_manager.backup_dlls(self.temp_dir, ["d3d11.dll"])
        
        # Check if backup was created
        backup_dir = os.path.join(self.temp_dir, "dxvk_backup")
        backup_file = os.path.join(backup_dir, "d3d11.dll")
        
        self.assertTrue(os.path.exists(backup_file))
        self.assertIn("d3d11.dll", backed_up)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    unittest.main()

