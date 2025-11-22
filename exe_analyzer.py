import os
import platform
from platform_utils import PlatformDetector

# Try to import pefile (Windows/Wine) and elftools (Linux native)
try:
    import pefile
    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False

try:
    from elftools.elf.elffile import ELFFile
    HAS_ELFTOOLS = True
except ImportError:
    HAS_ELFTOOLS = False

def get_exe_architecture(exe_path):
    """
    Analyzes the executable header to determine its architecture.
    Supports both Windows PE files and Linux ELF files.
    """
    if not os.path.exists(exe_path):
        return "File not found"
    
    # Try PE file format first (Windows executables or Wine)
    if HAS_PEFILE:
        try:
            pe = pefile.PE(exe_path)
            if pe.FILE_HEADER.Machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
                return "64-bit"
            elif pe.FILE_HEADER.Machine == 0x14c:  # IMAGE_FILE_MACHINE_I386
                return "32-bit"
            else:
                return "Unknown"
        except (pefile.PEFormatError, Exception):
            # Not a PE file, try ELF
            pass
    
    # Try ELF file format (Linux native executables)
    if HAS_ELFTOOLS and PlatformDetector.is_linux():
        try:
            with open(exe_path, 'rb') as f:
                elf = ELFFile(f)
                arch = elf.header['e_machine']
                if arch == 'EM_X86_64':
                    return "64-bit"
                elif arch == 'EM_386':
                    return "32-bit"
                else:
                    return "Unknown"
        except (Exception, OSError):
            pass
    
    # If we can't determine, return unknown
    if HAS_PEFILE or HAS_ELFTOOLS:
        return "Not a valid executable"
    else:
        return "Analysis library not available"

def detect_directx_version(game_folder):
    """
    Scans a folder for DirectX-related DLLs to infer the DirectX version.
    Works for both Windows and Wine prefixes (which use Windows DLLs).
    """
    dlls = {
        "d3d9.dll": "Direct3D 9",
        "d3d10.dll": "Direct3D 10",
        "d3d10core.dll": "Direct3D 10",
        "d3d11.dll": "Direct3D 11",
    }
    found_versions = []
    for dll, version in dlls.items():
        dll_path = os.path.join(game_folder, dll)
        if os.path.exists(dll_path):
            # Avoid duplicates
            if version not in found_versions:
                found_versions.append(version)
    return found_versions if found_versions else ["Unknown"]


