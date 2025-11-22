"""
Cross-platform utilities for OS detection and platform-specific operations.
"""
import os
import sys
import platform

class PlatformDetector:
    """Detects and provides platform-specific information."""
    
    @staticmethod
    def get_os():
        """Returns the operating system name."""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'unknown'
    
    @staticmethod
    def is_windows():
        """Check if running on Windows."""
        return PlatformDetector.get_os() == 'windows'
    
    @staticmethod
    def is_linux():
        """Check if running on Linux."""
        return PlatformDetector.get_os() == 'linux'
    
    @staticmethod
    def is_macos():
        """Check if running on macOS."""
        return PlatformDetector.get_os() == 'macos'
    
    @staticmethod
    def get_executable_extension():
        """Returns the executable file extension for the current platform."""
        if PlatformDetector.is_windows():
            return '.exe'
        elif PlatformDetector.is_linux() or PlatformDetector.is_macos():
            return ''  # Linux/Mac executables have no extension
        return '.exe'
    
    @staticmethod
    def get_library_extension():
        """Returns the library file extension for the current platform."""
        if PlatformDetector.is_windows():
            return '.dll'
        elif PlatformDetector.is_linux():
            return '.so'
        elif PlatformDetector.is_macos():
            return '.dylib'
        return '.dll'
    
    @staticmethod
    def find_wine_prefixes():
        """Finds Wine prefixes on Linux."""
        if not PlatformDetector.is_linux():
            return []
        
        wine_prefixes = []
        
        # Common Wine prefix locations
        home = os.path.expanduser('~')
        common_locations = [
            os.path.join(home, '.wine'),
            os.path.join(home, '.local', 'share', 'wineprefixes'),
            os.path.join(home, '.steam', 'steam', 'steamapps', 'compatdata'),
        ]
        
        # Check for WINEPREFIX environment variable
        wineprefix = os.environ.get('WINEPREFIX')
        if wineprefix and os.path.exists(wineprefix):
            wine_prefixes.append(wineprefix)
        
        # Check common locations
        for location in common_locations:
            if os.path.exists(location):
                if os.path.isdir(location):
                    # If it's a directory of prefixes
                    try:
                        for item in os.listdir(location):
                            item_path = os.path.join(location, item)
                            if os.path.isdir(item_path):
                                # Check if it looks like a Wine prefix
                                if os.path.exists(os.path.join(item_path, 'drive_c')):
                                    wine_prefixes.append(item_path)
                    except PermissionError:
                        pass
                else:
                    wine_prefixes.append(location)
        
        return wine_prefixes
    
    @staticmethod
    def is_wine_prefix(path):
        """Check if a path is a Wine prefix."""
        if not PlatformDetector.is_linux():
            return False
        
        # Wine prefix should have drive_c directory
        drive_c = os.path.join(path, 'drive_c')
        return os.path.exists(drive_c) and os.path.isdir(drive_c)
    
    @staticmethod
    def get_wine_game_path(wine_prefix, game_relative_path):
        """
        Converts a Windows game path to Wine prefix path.
        
        Args:
            wine_prefix: Path to Wine prefix (e.g., ~/.wine)
            game_relative_path: Windows-style path (e.g., C:/Games/MyGame)
        
        Returns:
            Linux path within Wine prefix
        """
        if not PlatformDetector.is_linux():
            return game_relative_path
        
        # Remove drive letter and convert to Wine path
        if game_relative_path.startswith('C:'):
            game_relative_path = game_relative_path[2:]
        elif game_relative_path.startswith('c:'):
            game_relative_path = game_relative_path[2:]
        
        # Normalize path separators
        game_relative_path = game_relative_path.replace('\\', '/')
        if game_relative_path.startswith('/'):
            game_relative_path = game_relative_path[1:]
        
        # Build full path
        full_path = os.path.join(wine_prefix, 'drive_c', game_relative_path)
        return os.path.normpath(full_path)

