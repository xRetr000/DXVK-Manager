import json
import os
from datetime import datetime

class Logger:
    def __init__(self, log_file="dxvk_manager_log.json"):
        self.log_file = log_file
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f) # Initialize with an empty list

    def log_installation(self, game_path, architecture, directx_version, dxvk_version):
        """Logs a DXVK installation event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "game_path": game_path,
            "architecture": architecture,
            "directx_version": directx_version,
            "dxvk_version": dxvk_version
        }
        self._append_to_log(log_entry)

    def _append_to_log(self, entry):
        with open(self.log_file, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0) # Rewind to the beginning
            json.dump(data, f, indent=4)
            f.truncate() # Truncate any remaining old content

    def get_logs(self):
        """Retrieves all log entries."""
        with open(self.log_file, "r") as f:
            return json.load(f)


