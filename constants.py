"""
Shared constants for DXVK Manager.
"""

# Maps DirectX version → list of DLLs to install/extract.
# DXVK does not ship d3d10.dll — it uses d3d10core.dll for D3D10 support.
# Direct3D 12 is handled by vkd3d-proton, not DXVK, and ships no dxgi.dll.
DLL_MAP = {
    'Direct3D 9':  ['d3d9.dll', 'dxgi.dll'],
    'Direct3D 10': ['d3d10core.dll', 'dxgi.dll'],
    'Direct3D 11': ['d3d11.dll', 'dxgi.dll'],
    'Direct3D 12': ['d3d12.dll', 'd3d12core.dll'],
    'Unknown':     ['d3d9.dll', 'd3d10core.dll', 'd3d11.dll', 'dxgi.dll'],
}

# Translation layers ("renderers") and the DirectX versions each one covers.
# A game is either D3D9/10/11 (DXVK) or D3D12 (vkd3d-proton), never both.
RENDERER_DXVK = 'dxvk'
RENDERER_VKD3D = 'vkd3d-proton'

RENDERER_NAMES = {
    RENDERER_DXVK: 'DXVK',
    RENDERER_VKD3D: 'vkd3d-proton',
}

RENDERER_DIRECTX_VERSIONS = {
    RENDERER_DXVK: ['Direct3D 9', 'Direct3D 10', 'Direct3D 11', 'Unknown'],
    RENDERER_VKD3D: ['Direct3D 12'],
}
