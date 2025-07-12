import os
import shutil

class FileManager:
    def __init__(self):
        pass

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """Copies specified DLLs from source to target directory."""
        for dll in dll_names:
            source_path = os.path.join(source_dir, dll)
            target_path = os.path.join(target_dir, dll)
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                print(f"Copied {dll} to {target_dir}")
            else:
                print(f"Warning: {dll} not found in {source_dir}")

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
        
        for item in os.listdir(backup_dir):
            backup_path = os.path.join(backup_dir, item)
            game_path = os.path.join(game_folder, item)
            if os.path.isfile(backup_path):
                shutil.copy2(backup_path, game_path)
                print(f"Restored {item} from backup.")
        shutil.rmtree(backup_dir) # Remove backup folder after restoration
        print("Backup folder removed.")
        return True


