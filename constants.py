"""
Shared constants for DXVK Manager.
"""

# Maps DirectX version → list of DLLs to install/extract.
# DXVK does not ship d3d10.dll — it uses d3d10core.dll for D3D10 support.
DLL_MAP = {
    'Direct3D 9':  ['d3d9.dll', 'dxgi.dll'],
    'Direct3D 10': ['d3d10core.dll', 'dxgi.dll'],
    'Direct3D 11': ['d3d11.dll', 'dxgi.dll'],
    'Unknown':     ['d3d9.dll', 'd3d10core.dll', 'd3d11.dll', 'dxgi.dll'],
}
