"""
Windows-only file manager with UAC and permission handling.
"""
import os
import shutil
import ctypes
import sys

MANIFEST_FILE = "installed_dlls.txt"

def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
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
        return False

def _clear_readonly(path):
    """Clear the FILE_ATTRIBUTE_READONLY flag on a Windows file using the Win32 API."""
    FILE_ATTRIBUTE_READONLY = 0x1
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attrs != -1 and (attrs & FILE_ATTRIBUTE_READONLY):
        ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs & ~FILE_ATTRIBUTE_READONLY)

class FileManager:
    def __init__(self):
        self.long_path_support = check_long_path_support()
        self.is_admin = is_admin()

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """
        Copies specified DLLs from source to target directory.
        Windows-specific: Handles permissions, UAC, and long paths.
        """
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

                # Clear read-only attribute if set (Windows ACL-aware)
                if os.path.exists(target_path):
                    _clear_readonly(target_path)

                    if not os.access(target_path, os.W_OK):
                        raise PermissionError(
                            f"Cannot write to {dll}. The file may be:\n"
                            f"- In use by the game (close the game first)\n"
                            f"- Protected by antivirus\n"
                            f"- In a read-only folder\n\n"
                            f"Try running as Administrator if the game is in Program Files."
                        )

                if not os.access(target_dir, os.W_OK):
                    raise PermissionError(
                        f"Cannot write to game folder: {target_dir}\n\n"
                        f"This folder may require administrator privileges.\n"
                        f"Try running DXVK Manager as Administrator."
                    )

                shutil.copy2(source_path, target_path)

                if not os.path.exists(target_path):
                    raise IOError(f"Failed to copy {dll}. File was not created.")

                copied_files.append(dll)
                print(f"Copied {dll} to {target_dir}")

            except PermissionError:
                raise
            except Exception as e:
                print(f"Error copying {dll}: {e}")
                raise ValueError(f"Failed to copy {dll}: {str(e)}")

        if not copied_files:
            raise ValueError("No DLLs were copied. Check file permissions and ensure the game is not running.")

        return copied_files

    def backup_dlls(self, target_dir, dll_names):
        """
        Creates a backup of existing DLLs in a subfolder and saves a manifest
        of all DLLs being installed so uninstall knows what to remove.
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

        # Save a manifest of which DLLs are being installed
        # so uninstall knows exactly what to remove even if no originals existed
        manifest_path = os.path.join(backup_dir, MANIFEST_FILE)
        try:
            with open(manifest_path, "w") as f:
                for dll in dll_names:
                    f.write(dll + "\n")
            print(f"Saved install manifest: {dll_names}")
        except Exception as e:
            raise IOError(f"Failed to write install manifest: {str(e)}")

        # Back up any original DLLs that already exist in the game folder
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
        else:
            print("No original DLLs found to back up (game didn't have them). Manifest saved for clean uninstall.")

        return backed_up_files

    def restore_dlls(self, game_folder):
        """
        Uninstalls DXVK by:
        1. Reading the manifest to find which DLLs were installed
        2. Deleting those DLLs from the game folder
        3. Restoring any original DLLs from backup
        4. Removing the backup folder
        """
        backup_dir = os.path.join(game_folder, "dxvk_backup")
        if not os.path.exists(backup_dir):
            print("No backup folder found.")
            return False

        if not os.path.isdir(backup_dir):
            print(f"Backup path exists but is not a directory: {backup_dir}")
            return False

        # Read the manifest to know which DLLs were installed
        manifest_path = os.path.join(backup_dir, MANIFEST_FILE)
        installed_dlls = []
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    installed_dlls = [line.strip() for line in f if line.strip()]
                print(f"Manifest found. DLLs to remove: {installed_dlls}")
            except Exception as e:
                print(f"Warning: Could not read manifest: {e}")
        else:
            print("Warning: No manifest found. Will only restore backed-up files.")

        try:
            # Step 1: Delete installed DXVK DLLs from game folder
            removed_files = []
            for dll in installed_dlls:
                game_path = os.path.join(game_folder, dll)
                if os.path.exists(game_path):
                    try:
                        _clear_readonly(game_path)
                        os.remove(game_path)
                        removed_files.append(dll)
                        print(f"Removed installed DXVK file: {dll}")
                    except Exception as e:
                        print(f"Warning: Could not remove {dll}: {e}")

            # Step 2: Restore original DLLs from backup (if any were backed up)
            restored_files = []
            for item in os.listdir(backup_dir):
                if item == MANIFEST_FILE:
                    continue  # Skip the manifest file
                backup_path = os.path.join(backup_dir, item)
                game_path = os.path.join(game_folder, item)
                if os.path.isfile(backup_path):
                    try:
                        if os.path.exists(game_path):
                            _clear_readonly(game_path)
                            if not os.access(game_path, os.W_OK):
                                raise PermissionError(f"Cannot write to {game_path}.")
                        shutil.copy2(backup_path, game_path)
                        restored_files.append(item)
                        print(f"Restored original {item} from backup.")
                    except Exception as e:
                        print(f"Error restoring {item}: {e}")
                        raise

            # Step 3: Clean up the backup folder
            shutil.rmtree(backup_dir)
            print(f"Backup folder removed.")

            if removed_files or restored_files:
                print(f"Uninstall complete. Removed: {removed_files}, Restored: {restored_files}")
                return True
            else:
                print("No files were removed or restored.")
                return False

        except Exception as e:
            print(f"Error during restore: {e}")
            return False
