import os
import shutil
import stat

class FileManager:
    def __init__(self):
        pass
    
    def _check_windows_permissions(self, path, is_file=True):
        """Check Windows file/folder permissions and provide user-friendly error messages."""
        if not os.path.exists(path):
            return True  # Can create new file
        
        # Check if path is in Program Files (requires admin)
        path_lower = path.lower()
        if 'program files' in path_lower or 'program files (x86)' in path_lower:
            if not os.access(path, os.W_OK):
                raise PermissionError(
                    f"Cannot write to {path}\n\n"
                    "This folder is in Program Files and requires administrator privileges.\n"
                    "Please:\n"
                    "1. Right-click DXVK Manager and select 'Run as administrator', OR\n"
                    "2. Move the game to a folder outside Program Files (e.g., C:\\Games)"
                )
        
        # Check if file is read-only
        if is_file:
            file_stat = os.stat(path)
            if file_stat.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                raise PermissionError(
                    f"Cannot write to {path}\n\n"
                    "The file is marked as read-only.\n"
                    "Please remove the read-only attribute or run as administrator."
                )
        
        # Check write access
        if not os.access(path, os.W_OK):
            raise PermissionError(
                f"Cannot write to {path}\n\n"
                "You don't have permission to modify files in this folder.\n"
                "Try:\n"
                "1. Running DXVK Manager as administrator\n"
                "2. Checking folder permissions\n"
                "3. Moving the game to a folder you own"
            )
        
        return True

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """Copies specified DLLs from source to target directory with Windows-specific error handling."""
        copied_files = []
        
        # Check target directory permissions first
        try:
            self._check_windows_permissions(target_dir, is_file=False)
        except PermissionError as e:
            raise PermissionError(str(e))
        
        for dll in dll_names:
            source_path = os.path.join(source_dir, dll)
            target_path = os.path.join(target_dir, dll)
            try:
                if not os.path.exists(source_path):
                    print(f"Warning: {dll} not found in {source_dir}")
                    continue
                
                # Check permissions before copying
                self._check_windows_permissions(target_path, is_file=True)
                
                # Copy the file
                shutil.copy2(source_path, target_path)
                copied_files.append(dll)
                print(f"Copied {dll} to {target_dir}")
                
            except PermissionError:
                raise  # Re-raise permission errors with user-friendly messages
            except Exception as e:
                error_msg = (
                    f"Failed to copy {dll}:\n"
                    f"Error: {str(e)}\n\n"
                    "Possible causes:\n"
                    "- File is in use by another program\n"
                    "- Insufficient permissions\n"
                    "- Antivirus is blocking the operation"
                )
                raise RuntimeError(error_msg) from e
        
        if not copied_files:
            raise ValueError(
                "No DLLs were copied.\n\n"
                "Possible causes:\n"
                "- Source DLLs not found\n"
                "- Insufficient permissions\n"
                "- Files are locked by another program"
            )
        
        return copied_files

    def backup_dlls(self, target_dir, dll_names):
        """Creates a backup of existing DLLs in a subfolder."""
        backup_dir = os.path.join(target_dir, "dxvk_backup")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except PermissionError:
            raise PermissionError(
                f"Cannot create backup folder in {target_dir}\n\n"
                "You don't have permission to create folders here.\n"
                "Try running DXVK Manager as administrator."
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
                    print(f"Warning: Could not backup {dll}: {e}")
                    # Continue with other DLLs even if one backup fails
        
        if not backed_up_files:
            print("Warning: No DLLs were backed up (they may not exist yet)")
        
        return backed_up_files

    def create_symlink(self, source_path, link_path):
        """Creates a symbolic link (Windows 10+). Not used in current implementation."""
        # This method is kept for potential future use but not currently called
        try:
            os.symlink(source_path, link_path)
            print(f"Created symlink from {source_path} to {link_path}")
            return True
        except OSError as e:
            print(f"Error creating symlink: {e}. Admin privileges might be required.")
            return False

    def restore_dlls(self, game_folder):
        """Restores DLLs from the backup folder with Windows-specific error handling."""
        backup_dir = os.path.join(game_folder, "dxvk_backup")
        if not os.path.exists(backup_dir):
            print("No backup found. DXVK may not have been installed, or backup was removed.")
            return False
        
        if not os.path.isdir(backup_dir):
            print(f"Backup path exists but is not a directory: {backup_dir}")
            return False
        
        restored_files = []
        try:
            # Check permissions before starting restore
            self._check_windows_permissions(game_folder, is_file=False)
            
            for item in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, item)
                game_path = os.path.join(game_folder, item)
                if os.path.isfile(backup_path):
                    try:
                        # Check write permissions
                        self._check_windows_permissions(game_path, is_file=True)
                        
                        shutil.copy2(backup_path, game_path)
                        restored_files.append(item)
                        print(f"Restored {item} from backup.")
                    except PermissionError:
                        raise  # Re-raise with user-friendly message
                    except Exception as e:
                        error_msg = (
                            f"Failed to restore {item}:\n"
                            f"Error: {str(e)}\n\n"
                            "The file may be in use or you may need administrator privileges."
                        )
                        raise RuntimeError(error_msg) from e
            
            if restored_files:
                try:
                    shutil.rmtree(backup_dir)  # Remove backup folder after restoration
                    print(f"Backup folder removed. Restored {len(restored_files)} file(s).")
                except Exception as e:
                    print(f"Warning: Could not remove backup folder: {e}")
                    print("You can safely delete it manually if needed.")
                return True
            else:
                print("No files were restored from backup.")
                return False
                
        except PermissionError:
            raise  # Re-raise permission errors
        except Exception as e:
            error_msg = (
                f"Error during restore: {str(e)}\n\n"
                "Possible causes:\n"
                "- Insufficient permissions (try running as administrator)\n"
                "- Files are locked by another program\n"
                "- Backup folder is corrupted"
            )
            raise RuntimeError(error_msg) from e


