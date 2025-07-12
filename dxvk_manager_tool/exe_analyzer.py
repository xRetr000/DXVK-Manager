import os
import pefile

def get_exe_architecture(exe_path):
    """Analyzes the PE header of an executable to determine its architecture."""
    try:
        pe = pefile.PE(exe_path)
        if pe.FILE_HEADER.Machine == 0x8664: # IMAGE_FILE_MACHINE_AMD64
            return "64-bit"
        elif pe.FILE_HEADER.Machine == 0x14c: # IMAGE_FILE_MACHINE_I386
            return "32-bit"
        else:
            return "Unknown"
    except pefile.PEFormatError:
        return "Not a valid PE file"

def detect_directx_version(game_folder):
    """Scans a folder for DirectX-related DLLs to infer the DirectX version."""
    dlls = {
        "d3d9.dll": "Direct3D 9",
        "d3d10.dll": "Direct3D 10",
        "d3d11.dll": "Direct3D 11",
    }
    found_versions = []
    for dll, version in dlls.items():
        if os.path.exists(os.path.join(game_folder, dll)):
            found_versions.append(version)
    return found_versions if found_versions else ["Unknown"]


