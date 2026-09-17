# DXVK Manager

DXVK Manager supports installing DirectX translation layers into a selected Windows game folder.

Supported sources:

- Official DXVK from [doitsujin/dxvk](https://github.com/doitsujin/dxvk)
- DXVK GPLAsync from [Ph42oN/dxvk-gplasync](https://gitlab.com/Ph42oN/dxvk-gplasync)
- vkd3d-proton from [HansKristian-Work/vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton)

vkd3d-proton is for Direct3D 12 games and installs `d3d12.dll` and `d3d12core.dll` from the selected release. Its releases use `.tar.zst` archives, so the `zstandard` dependency is required.

Install dependencies with:

```bash
pip install -r requirements.txt
```

Run the application with:

```bash
python dxvk_manager.py
```

Always close the game before installing or restoring DLLs. The application creates a backup manifest so installed files can be restored.
