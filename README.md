# DXVK Manager

A Windows tool for automatically downloading and installing DXVK into your game folders.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

---

## Download & Run

Grab `DXVK_Manager.exe` from [Releases](https://github.com/xRetr000/DXVK-Manager/releases) and double-click it. No Python or dependencies needed.

---

## What it does

1. You point it at a game folder
2. It detects the architecture (32-bit / 64-bit) and DirectX version
3. Downloads the latest DXVK from GitHub
4. Backs up your existing DLLs and installs DXVK

To uninstall, select the same folder and hit "Uninstall DXVK" — it restores from backup.

---

## Build from source

```bash
pip install -r requirements.txt
python dxvk_manager.py
```

Or build the exe yourself:

```
BUILD.bat
```

---

## Troubleshooting

**Game won't start after install** — click "Uninstall DXVK" to restore original files.

**Download fails** — check your internet connection or try running as administrator.

**Wrong DirectX version detected** — use the override dropdown to set it manually.

---

## Linux

> **Linux support is on hold and not a priority.**
>
> If you're on Linux, you don't need this tool — just use **Proton**, **Lutris**, or **Steam**. They handle DXVK automatically and do it better than this ever will.

---

## License

Apache 2.0. DXVK itself is licensed under zlib/libpng.
