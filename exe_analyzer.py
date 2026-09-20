"""
Windows-only executable analyzer for PE files.
"""
import os
import re
import pefile

# DirectX runtime DLL → API version. d3d10.dll and d3d10core.dll both mean D3D10.
DIRECTX_DLLS = {
    "d3d9.dll": "Direct3D 9",
    "d3d10.dll": "Direct3D 10",
    "d3d10core.dll": "Direct3D 10",
    "d3d11.dll": "Direct3D 11",
    "d3d12.dll": "Direct3D 12",
}

# Matches DirectX DLL names as ASCII or UTF-16LE strings inside a binary
_DX_STRING_RE = re.compile(
    rb"d3d(?:9|10|10core|11|12)\.dll|d\x00" + rb"3\x00d\x00(?:9|1\x000\x00|1\x001\x00|1\x002\x00)\.\x00d\x00l\x00l\x00",
    re.IGNORECASE,
)

# How many sibling DLLs (largest first) to inspect for D3D imports. Engines like
# Unity/Unreal/Godot do their D3D work in a big runtime DLL, not the .exe itself.
_MAX_SIBLING_DLLS = 20

def get_exe_files(game_folder):
    """
    Returns a list of all .exe files found in the given folder.
    Useful for letting the user pick the correct executable when multiple exist.
    """
    if not os.path.isdir(game_folder):
        return []
    return [f for f in os.listdir(game_folder) if f.lower().endswith(".exe")]


def get_best_exe(game_folder):
    """
    Attempts to auto-select the best .exe by picking the largest file.
    Falls back to the first .exe if sizes are equal.
    Returns the full path or None if no .exe found.
    """
    exe_files = get_exe_files(game_folder)
    if not exe_files:
        return None
    best = max(exe_files, key=lambda f: os.path.getsize(os.path.join(game_folder, f)))
    return os.path.join(game_folder, best)


def get_exe_architecture(exe_path):
    """
    Analyzes the PE (Portable Executable) header to determine architecture.
    Windows-only: Only supports PE files (.exe, .dll).
    """
    if not os.path.exists(exe_path):
        return "File not found"
    
    try:
        pe = pefile.PE(exe_path)
        if pe.FILE_HEADER.Machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
            return "64-bit"
        elif pe.FILE_HEADER.Machine == 0x14c:  # IMAGE_FILE_MACHINE_I386
            return "32-bit"
        else:
            return "Unknown"
    except pefile.PEFormatError:
        return "Not a valid PE file"
    except Exception as e:
        return f"Error: {str(e)}"

def get_pe_imports(pe_path):
    """
    Returns the lowercase set of DLL names a PE file imports, parsing only the
    import directory so large engine DLLs are cheap to inspect. Empty on failure.
    """
    try:
        pe = pefile.PE(pe_path, fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        imports = set()
        for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            if entry.dll:
                imports.add(entry.dll.decode("ascii", errors="ignore").lower())
        pe.close()
        return imports
    except Exception:
        return set()


def _versions_from_dll_names(dll_names):
    """Maps a collection of DLL names to an ordered, de-duplicated list of DirectX versions."""
    versions = []
    for dll in DIRECTX_DLLS:  # iterate in a stable order (D3D9 → D3D12)
        if dll in dll_names and DIRECTX_DLLS[dll] not in versions:
            versions.append(DIRECTX_DLLS[dll])
    return versions


def _installed_by_us(game_folder):
    """DLLs recorded in our backup manifest — these are DXVK/vkd3d-proton's, not the game's."""
    manifest = os.path.join(game_folder, "dxvk_backup", "installed_dlls.txt")
    try:
        with open(manifest, "r") as f:
            return {line.strip().lower() for line in f if line.strip()}
    except OSError:
        return set()


def _scan_strings_for_dx_dlls(path, max_bytes=256 * 1024 * 1024):
    """Finds DirectX DLL names mentioned as strings (e.g. LoadLibrary targets) in a binary."""
    found = set()
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        for m in _DX_STRING_RE.finditer(data):
            found.add(m.group(0).replace(b"\x00", b"").decode("ascii", errors="ignore").lower())
    except OSError:
        pass
    return found


def detect_directx_details(game_folder, exe_path=None):
    """
    Infers which Direct3D API(s) a game uses. Returns {"versions": [...], "method": str}.

    Detection sources, most to least reliable:
      1. The import table of the game .exe
      2. The import tables of the largest DLLs beside it (engine runtimes such as
         UnityPlayer.dll do the D3D work, not the .exe)
      3. DirectX DLLs shipped in the game folder, ignoring ones we installed ourselves
      4. DirectX DLL names appearing as strings in the .exe (dynamic LoadLibrary);
         this is noisy — engines often mention every API they *could* use
    """
    if exe_path is None:
        exe_path = get_best_exe(game_folder)

    ours = _installed_by_us(game_folder)

    # 1. Import table of the executable
    if exe_path and os.path.isfile(exe_path):
        versions = _versions_from_dll_names(get_pe_imports(exe_path))
        if versions:
            return {"versions": versions, "method": "exe imports"}

    # 2. Import tables of sibling engine DLLs
    try:
        sibling_dlls = [
            os.path.join(game_folder, f) for f in os.listdir(game_folder)
            if f.lower().endswith(".dll")
            and f.lower() not in DIRECTX_DLLS and f.lower() != "dxgi.dll"
        ]
    except OSError:
        sibling_dlls = []
    sibling_dlls.sort(key=os.path.getsize, reverse=True)
    for dll_path in sibling_dlls[:_MAX_SIBLING_DLLS]:
        versions = _versions_from_dll_names(get_pe_imports(dll_path))
        if versions:
            return {"versions": versions, "method": f"{os.path.basename(dll_path)} imports"}

    # 3. DirectX DLLs present in the game folder (excluding what DXVK Manager installed)
    present = {
        dll for dll in DIRECTX_DLLS
        if dll not in ours and os.path.exists(os.path.join(game_folder, dll))
    }
    versions = _versions_from_dll_names(present)
    if versions:
        return {"versions": versions, "method": "DLLs in game folder"}

    # 4. String references inside the executable
    if exe_path and os.path.isfile(exe_path):
        versions = _versions_from_dll_names(_scan_strings_for_dx_dlls(exe_path))
        if versions:
            return {"versions": versions, "method": "strings in exe (low confidence)"}

    return {"versions": ["Unknown"], "method": "none"}


def detect_directx_version(game_folder, exe_path=None):
    """
    Infers the DirectX version(s) a game uses. Returns a list such as
    ["Direct3D 11"] or ["Unknown"]. See detect_directx_details() for how.
    """
    return detect_directx_details(game_folder, exe_path)["versions"]
