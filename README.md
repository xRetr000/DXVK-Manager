<h1 align="center">
  <img width="128" height="128" alt="DXVK Manager icon" src="https://github.com/user-attachments/assets/0a0b3a1d-2903-45c4-acb8-c00ceaa2c5d1" />
  <br>
  DXVK Manager
</h1>

<p align="center">
  A Windows GUI tool for installing, configuring, and managing DXVK — no terminal, no manual DLL copying.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
</p>

<p align="center">
<img width="1346" height="904" alt="image" src="https://github.com/user-attachments/assets/04244275-d2f1-4499-8f8a-b2e4d17def07" />
</p>

---

## Download & Run

Grab `DXVK_Manager.exe` from [Releases](https://github.com/xRetr000/DXVK-Manager/releases) and double-click it.
No Python, no dependencies, no setup.

---

## Features

- **One-click install** — point it at a game folder and DXVK is downloaded, extracted, and installed automatically
- **Auto-detection** — architecture (32-bit / 64-bit) and DirectX version are detected from the game's `.exe`, with a manual override if needed
- **Multiple executables handled** — if a folder has several `.exe` files, you pick the right one instead of guessing wrong
- **Choose your DXVK source and version** — install from the official [doitsujin/dxvk](https://github.com/doitsujin/dxvk) or the [GPLAsync](https://gitlab.com/Ph42oN/dxvk-gplasync) fork, and pick a specific release instead of always grabbing latest
- **Built-in dxvk.conf editor** — tune HUD display, async shader compilation, frame rate cap, VRAM budget, Tear-Free, shader cache, and log level from a GUI, no text file editing
- **PCGamingWiki integration** — jump straight to a game's compatibility page with one click
- **Safe by design** — original DLLs are always backed up before anything is touched, and restored cleanly on uninstall
- **Modern dark UI** — clean, card-based layout throughout

---

## What it does

1. You point it at a game folder
2. It detects the architecture and DirectX version (or you set them manually)
3. Downloads your chosen DXVK release (official or GPLAsync, latest or a specific version)
4. Backs up your existing DLLs and installs DXVK

To uninstall, select the same folder and hit **Uninstall DXVK** — it restores your original files from backup.

---

## Build from source

```bash
pip install -r requirements.txt
python dxvk_manager.py
```

Or build the exe yourself:

```bash
BUILD.bat
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Game won't start after install | Click **Uninstall DXVK** to restore the original files |
| Download fails | Check your internet connection, or try running as administrator |
| Wrong DirectX version detected | Use the override dropdown to set it manually |
| Wrong `.exe` picked | Use the executable picker dialog to select the correct one |
| Backup folder is empty | This is expected if the game had no original DirectX DLLs — DXVK's files are still tracked and removed cleanly on uninstall |

---

## Linux

> **Linux support is on hold and not a priority.**
>
> If you're on Linux, you don't need this tool — just use **Proton**, **Lutris**, or **Steam**. They handle DXVK automatically and do it better than this ever will.

---

## Contributing

Found a bug or have a feature idea? Open an [issue](https://github.com/xRetr000/DXVK-Manager/issues) — feedback from users has directly shaped features like the config editor and executable picker.

---

## License

Apache 2.0. DXVK itself is licensed under zlib/libpng.
