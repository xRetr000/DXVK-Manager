"""
Windows-only utilities for OS detection and platform-specific operations.
"""
import os
import sys
import platform

class PlatformDetector:
    """Windows platform detection utilities."""
    
    @staticmethod
    def get_os():
        """Returns 'windows' if running on Windows."""
        system = platform.system().lower()
        return 'windows' if system == 'windows' else 'unknown'
    
    @staticmethod
    def is_windows():
        """Check if running on Windows."""
        return platform.system().lower() == 'windows'
    
    @staticmethod
    def get_executable_extension():
        """Returns '.exe' for Windows executables."""
        return '.exe'
    
    @staticmethod
    def get_library_extension():
        """Returns '.dll' for Windows libraries."""
        return '.dll'
