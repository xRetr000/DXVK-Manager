"""
Windows-only file manager with UAC and permission handling.
"""
import os
import shutil
import ctypes
import sys

def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def check_long_path_support():
    """Check if long path support is enabled (Windows 10 1607+)."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SYSTEM\CurrentControlSet\Control\FileSystem")
        long_paths = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
        winreg.CloseKey(key)
        return long_paths == 1
    except (FileNotFoundError, OSError, ValueError):
        # Registry key doesn't exist or access denied
        return False

class FileManager:
    def __init__(self):
        self.long_path_support = check_long_path_support()
        self.is_admin = is_admin()

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """
        Copies specified DLLs from source to target directory.
        Windows-specific: Handles permissions, UAC, and long paths.
        """
        # Check if target is in Program Files (needs admin)
        program_files_paths = [
            os.path.expandvars("%ProgramFiles%"),
            os.path.expandvars("%ProgramFiles(x86)%"),
            os.path.expandvars("%ProgramW6432%"),
        ]
        needs_admin = any(target_dir.startswith(pf) for pf in program_files_paths if pf)
        
        if needs_admin and not self.is_admin:
            raise PermissionError(
                f"Game folder is in Program Files. Administrator privileges required.\n\n"
                f"Please run DXVK Manager as Administrator:\n"
                f"1. Right-click DXVK_Manager.exe\n"
                f"2. Select 'Run as administrator'\n"
                f"3. Try again"
            )
        
        copied_files = []
        for dll in dll_names:
            source_path = os.path.join(source_dir, dll)
            target_path = os.path.join(target_dir, dll)
            
            try:
                if not os.path.exists(source_path):
                    print(f"Warning: {dll} not found in {source_dir}")
                    continue
                
                # Check if target file exists and is read-only
                if os.path.exists(target_path):
                    # Remove read-only attribute if set
                    try:
                        os.chmod(target_path, 0o666)
                    except:
                        pass
                    
                    if not os.access(target_path, os.W_OK):
                        error_msg = (
                            f"Cannot write to {dll}. The file may be:\n"
                            f"- In use by the game (close the game first)\n"
                            f"- Protected by antivirus\n"
                            f"- In a read-only folder\n\n"
                            f"Try running as Administrator if the game is in Program Files."
                        )
                        raise PermissionError(error_msg)
                
                # Check directory permissions
                if not os.access(target_dir, os.W_OK):
                    raise PermissionError(
                        f"Cannot write to game folder: {target_dir}\n\n"
                        f"This folder may require administrator privileges.\n"
                        f"Try running DXVK Manager as Administrator."
                    )
                
                # Copy the file
                shutil.copy2(source_path, target_path)
                
                # Verify copy succeeded
                if not os.path.exists(target_path):
                    raise IOError(f"Failed to copy {dll}. File was not created.")
                
                copied_files.append(dll)
                print(f"Copied {dll} to {target_dir}")
                
            except PermissionError:
                raise  # Re-raise permission errors with our custom messages
            except Exception as e:
                print(f"Error copying {dll}: {e}")
                raise ValueError(f"Failed to copy {dll}: {str(e)}")
        
        if not copied_files:
            raise ValueError("No DLLs were copied. Check file permissions and ensure the game is not running.")
        
        return copied_files

    def backup_dlls(self, target_dir, dll_names):
        """
        Creates a backup of existing DLLs in a subfolder.
        Always creates backup - safety first for Windows users.
        """
        backup_dir = os.path.join(target_dir, "dxvk_backup")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except PermissionError:
            raise PermissionError(
                f"Cannot create backup folder in {target_dir}.\n\n"
                f"You may need administrator privileges.\n"
                f"Try running DXVK Manager as Administrator."
            )
        
        backed_up_files = []
        for dll in dll_names:
            source_path = os.path.join(target_dir, dll)
            if os.path.exists(source_path):
                try:
                    backup_path = os.path.join(backup_dir, dll)
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(dll)
                    print(f"Backed up {dll} to {backup_dir}")
                except Exception as e:
                    raise IOError(f"Failed to backup {dll}: {str(e)}")
        
        if backed_up_files:
            print(f"Created backup of {len(backed_up_files)} file(s) in {backup_dir}")
        
        return backed_up_files

    def create_symlink(self, source_path, link_path):
        """Creates a symbolic link (Windows 10+)."""
        try:
            # For files, use junction on Windows for directories, symlink for files
            # os.symlink requires admin privileges on Windows by default
            # For simplicity, we'll assume file symlinks are intended here.
            os.symlink(source_path, link_path)
            print(f"Created symlink from {source_path} to {link_path}")
            return True
        except OSError as e:
            print(f"Error creating symlink: {e}. Admin privileges might be required.")
            return False

    def restore_dlls(self, game_folder):
        """Restores DLLs from the backup folder."""
        backup_dir = os.path.join(game_folder, "dxvk_backup")
        if not os.path.exists(backup_dir):
            print("No backup found.")
            return False
        
        if not os.path.isdir(backup_dir):
            print(f"Backup path exists but is not a directory: {backup_dir}")
            return False
        
        restored_files = []
        try:
            for item in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, item)
                game_path = os.path.join(game_folder, item)
                if os.path.isfile(backup_path):
                    try:
                        # Check write permissions
                        if os.path.exists(game_path) and not os.access(game_path, os.W_OK):
                            raise PermissionError(f"Cannot write to {game_path}. Check file permissions.")
                        
                        shutil.copy2(backup_path, game_path)
                        restored_files.append(item)
                        print(f"Restored {item} from backup.")
                    except Exception as e:
                        print(f"Error restoring {item}: {e}")
                        raise
            
            if restored_files:
                shutil.rmtree(backup_dir)  # Remove backup folder after restoration
                print(f"Backup folder removed. Restored {len(restored_files)} file(s).")
                return True
            else:
                print("No files were restored from backup.")
                return False
                
        except Exception as e:
            print(f"Error during restore: {e}")
            return False


