import os
import shutil

class FileManager:
    def __init__(self):
        pass

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """Copies specified DLLs from source to target directory."""
        copied_files = []
        for dll in dll_names:
            source_path = os.path.join(source_dir, dll)
            target_path = os.path.join(target_dir, dll)
            try:
                if os.path.exists(source_path):
                    # Check if target is writable
                    if os.path.exists(target_path):
                        if not os.access(target_path, os.W_OK):
                            raise PermissionError(f"Cannot write to {target_path}. Check file permissions.")
                    else:
                        if not os.access(target_dir, os.W_OK):
                            raise PermissionError(f"Cannot write to directory {target_dir}. Check folder permissions.")
                    
                    shutil.copy2(source_path, target_path)
                    copied_files.append(dll)
                    print(f"Copied {dll} to {target_dir}")
                else:
                    print(f"Warning: {dll} not found in {source_dir}")
            except Exception as e:
                print(f"Error copying {dll}: {e}")
                raise
        
        if not copied_files:
            raise ValueError("No DLLs were copied. Check source directory and file permissions.")
        
        return copied_files

    def backup_dlls(self, target_dir, dll_names):
        """Creates a backup of existing DLLs in a subfolder."""
        backup_dir = os.path.join(target_dir, "dxvk_backup")
        os.makedirs(backup_dir, exist_ok=True)
        backed_up_files = []
        for dll in dll_names:
            source_path = os.path.join(target_dir, dll)
            if os.path.exists(source_path):
                shutil.copy2(source_path, backup_dir)
                backed_up_files.append(dll)
                print(f"Backed up {dll} to {backup_dir}")
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


