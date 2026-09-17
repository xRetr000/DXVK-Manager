"""
Shared constants for DXVK Manager.
"""

# Maps DirectX version -> DLLs to install/extract for the selected source.
DXVK_DLL_MAP = {
    "Direct3D 9": ["d3d9.dll", "dxgi.dll"],
    "Direct3D 10": ["d3d10core.dll", "dxgi.dll"],
    "Direct3D 11": ["d3d11.dll", "dxgi.dll"],
    "Unknown": ["d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll"],
}

VKD3D_PROTON_DLL_MAP = {
    "Direct3D 12": ["d3d12.dll", "d3d12core.dll"],
    # vkd3d-proton only implements D3D12, so this is also the safe fallback
    # when automatic DirectX detection has not identified a version yet.
    "Unknown": ["d3d12.dll", "d3d12core.dll"],
}

# Backward-compatible name used by older callers.
DLL_MAP = DXVK_DLL_MAP

SOURCE_DLL_MAPS = {
    "official": DXVK_DLL_MAP,
    "gplasync": DXVK_DLL_MAP,
    "vkd3d-proton": VKD3D_PROTON_DLL_MAP,
}


def get_dll_map(source):
    """Return the DLL mapping for a source key."""
    return SOURCE_DLL_MAPS.get(source, DXVK_DLL_MAP)
