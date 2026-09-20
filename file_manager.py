"""
Windows-only file manager with UAC and permission handling.
"""
import os
import shutil
import ctypes
import sys
import tempfile

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

    @staticmethod
    def can_write_to(directory):
        """Checks real write access by creating and removing a temporary file."""
        try:
            fd, probe = tempfile.mkstemp(prefix=".dxvk_manager_probe_", dir=directory)
            os.close(fd)
            os.remove(probe)
            return True
        except OSError:
            return False

    @staticmethod
    def _is_under_program_files(directory):
        """True if directory lives under any Program Files root (case-insensitive)."""
        roots = [
            os.path.expandvars(v) for v in ("%ProgramFiles%", "%ProgramFiles(x86)%", "%ProgramW6432%")
        ]
        target = os.path.normcase(os.path.abspath(directory))
        return any(
            r and not r.startswith("%") and target.startswith(os.path.normcase(os.path.abspath(r)) + os.sep)
            for r in roots
        )

    def copy_dlls(self, source_dir, target_dir, dll_names):
        """
        Copies specified DLLs from source to target directory.
        Windows-specific: Handles permissions, UAC, and long paths.
        """
        # Probe for write access instead of guessing from the path: many folders
        # under Program Files (e.g. Steam's library) are user-writable, and
        # os.access() doesn't reflect Windows ACLs reliably.
        if not self.can_write_to(target_dir):
            hint = ""
            if self._is_under_program_files(target_dir) and not self.is_admin:
                hint = (
                    "\n\nThe game folder is in Program Files, so administrator privileges are likely required:\n"
                    "1. Right-click DXVK_Manager.exe\n"
                    "2. Select 'Run as administrator'\n"
                    "3. Try again"
                )
            raise PermissionError(f"Cannot write to game folder: {target_dir}{hint}")

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

    def read_manifest(self, target_dir):
        """Returns the list of DLLs recorded as installed in target_dir, or [] if none."""
        manifest_path = os.path.join(target_dir, "dxvk_backup", MANIFEST_FILE)
        if not os.path.exists(manifest_path):
            return []
        try:
            with open(manifest_path, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Warning: Could not read manifest: {e}")
            return []

    def backup_dlls(self, target_dir, dll_names):
        """
        Creates a backup of existing DLLs in a subfolder and saves a manifest
        of all DLLs being installed so uninstall knows what to remove.

        Safe to call again on a folder that already has a backup (e.g. upgrading
        DXVK, or adding vkd3d-proton next to DXVK): the first backup of each DLL
        is kept, since anything already in the game folder after that is ours,
        and the manifest is merged rather than overwritten.
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
        # so uninstall knows exactly what to remove even if no originals existed.
        # Merge with any previous install so nothing gets orphaned on uninstall.
        previously_installed = self.read_manifest(target_dir)
        manifest_dlls = previously_installed + [d for d in dll_names if d not in previously_installed]
        manifest_path = os.path.join(backup_dir, MANIFEST_FILE)
        try:
            with open(manifest_path, "w") as f:
                for dll in manifest_dlls:
                    f.write(dll + "\n")
            print(f"Saved install manifest: {manifest_dlls}")
        except Exception as e:
            raise IOError(f"Failed to write install manifest: {str(e)}")

        # Back up any original DLLs that already exist in the game folder.
        # A DLL we previously installed is NOT an original, so never overwrite an
        # existing backup and never back up something our own manifest lists.
        backed_up_files = []
        skipped_files = []
        for dll in dll_names:
            source_path = os.path.join(target_dir, dll)
            backup_path = os.path.join(backup_dir, dll)
            if not os.path.exists(source_path):
                continue
            if os.path.exists(backup_path) or dll in previously_installed:
                skipped_files.append(dll)
                continue
            try:
                shutil.copy2(source_path, backup_path)
                backed_up_files.append(dll)
                print(f"Backed up {dll} to {backup_dir}")
            except Exception as e:
                raise IOError(f"Failed to backup {dll}: {str(e)}")

        if skipped_files:
            print(f"Kept existing backup for: {', '.join(skipped_files)} (already installed by DXVK Manager)")
        if backed_up_files:
            print(f"Created backup of {len(backed_up_files)} file(s) in {backup_dir}")
        elif not skipped_files:
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
        installed_dlls = self.read_manifest(game_folder)
        if installed_dlls:
            print(f"Manifest found. DLLs to remove: {installed_dlls}")
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
