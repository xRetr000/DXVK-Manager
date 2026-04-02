import json
import os
import threading
from datetime import datetime, timezone

_MAX_LOG_ENTRIES = 500

class Logger:
    def __init__(self, log_file="dxvk_manager_log.json"):
        self.log_file = log_file
        self._lock = threading.Lock()
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f)

    def _read_log(self, f):
        """Read and parse the log file, resetting it if the JSON is corrupted."""
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

    def log_installation(self, game_path, architecture, directx_version, dxvk_version):
        """Logs a DXVK installation event."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "game_path": game_path,
            "architecture": architecture,
            "directx_version": directx_version,
            "dxvk_version": dxvk_version,
        }
        self._append_to_log(log_entry)

    def _append_to_log(self, entry):
        with self._lock:
            with open(self.log_file, "r+") as f:
                data = self._read_log(f)
                data.append(entry)
                # Cap log size to prevent unbounded growth
                if len(data) > _MAX_LOG_ENTRIES:
                    data = data[-_MAX_LOG_ENTRIES:]
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()

    def get_logs(self):
        """Retrieves all log entries."""
        with self._lock:
            try:
                with open(self.log_file, "r") as f:
                    return self._read_log(f)
            except FileNotFoundError:
                return []
