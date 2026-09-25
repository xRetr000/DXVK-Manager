# Changelog

All notable changes to the DXVK Manager Tool will be documented in this file.

## [1.1.0] - 2026-09-25

### Added
- **Direct3D 12 support via vkd3d-proton.** DXVK doesn't cover D3D12, so D3D12
  games now install [vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton)
  (`d3d12.dll` + `d3d12core.dll`) instead. A **Renderer** selector sits above the
  source dropdown and picks between DXVK (D3D9/10/11) and vkd3d-proton (D3D12);
  the source and version lists follow the renderer you choose.
- Detection now pre-selects vkd3d-proton for D3D12-only games, and a manual
  DirectX override always wins over auto-detection.
- Installing a source that can't handle the game's DirectX version is refused
  up front, before anything is downloaded.
- Extraction support for `.tar.zst` archives (the format vkd3d-proton ships),
  adding a `zstandard` dependency.
- Install log entries now record which renderer was used.
- Release builds are produced by a tag-triggered GitHub Actions workflow.

### Fixed
- **Reinstalling no longer destroys the original DLL backup.** Upgrading DXVK
  (or adding vkd3d-proton alongside it) without uninstalling first used to copy
  the *previously installed* DLL over the backup, permanently losing the game's
  original file. The first backup of each DLL is now kept, and the install
  manifest is merged across installs so uninstall removes everything.
- **DirectX detection actually works now.** It previously only looked for
  `d3d*.dll` files sitting in the game folder — which most games don't ship —
  and was fooled by DXVK's own DLLs after an install. It now reads the PE import
  table of the game executable and of the largest sibling DLLs (engines like
  Unity do their Direct3D work in a runtime DLL, not the `.exe`), falling back to
  shipped DLLs and then to string references. The log says which method was used.
- **No more spurious "run as Administrator" errors.** Write access is now checked
  by actually attempting a write instead of guessing from a Program Files path
  prefix, so user-writable Steam libraries under `Program Files (x86)` just work.
- The build script no longer aborts when a previous `build/` folder is briefly
  locked by antivirus or Explorer, and it now reports failure via its exit code
  so `BUILD.bat` stops claiming success after a failed build.
- CI was failing on every run (it ran on Linux, where `FileManager` can't import
  `winreg`); it now runs on Windows, matching the only platform the tool supports.

### Changed
- Install / Restore and Save / Reset buttons are pinned below the scroll area so
  they're always visible — previously the Install button could sit below the fold.
- The two panels are in a resizable splitter, and window size, position and split
  are remembered between sessions.
- Form labels are no longer drawn inside input-like boxes, and sections are flat
  headers instead of nested cards.
- Minimum Python version is now 3.10 (PyQt6 requires 3.8+; 3.10–3.12 are tested).

## [1.0.0] - 2024-01-15

### Added
- Initial release of DXVK Manager Tool
- Automatic game architecture detection (32-bit/64-bit) via PE header analysis
- DirectX version detection by scanning for existing DLLs (d3d9.dll, d3d10.dll, d3d11.dll)
- Automatic download of latest DXVK releases from GitHub
- Smart installation of appropriate DXVK DLLs based on game requirements
- Automatic backup creation before installing DXVK
- Complete uninstallation with backup restoration
- JSON-based installation logging
- Intuitive Tkinter-based GUI with:
  - Game folder browser
  - Auto-detection display
  - Manual DirectX version override
  - Backup option toggle
  - Real-time status messages
  - Installation progress tracking
- Comprehensive error handling and user feedback
- Unit tests for core modules
- Integration tests for complete workflow
- Detailed documentation and troubleshooting guide

### Features
- **Core Functionality:**
  - Browse and select game folders
  - PE header analysis for architecture detection
  - DirectX DLL scanning for version detection
  - GitHub API integration for latest DXVK downloads
  - Intelligent DLL extraction and installation
  
- **Safety Features:**
  - Automatic backup of existing DLLs
  - Safe uninstallation with backup restoration
  - Installation activity logging
  - Error handling and recovery
  
- **User Experience:**
  - Clean, intuitive GUI design
  - Real-time status updates
  - Manual override options
  - Comprehensive help documentation

### Technical Details
- Built with Python 3.7+ and Tkinter
- Modular architecture with separate concerns
- Cross-platform compatible (Windows focus)
- Minimal dependencies (pefile, requests)
- Comprehensive test coverage

### Known Limitations
- Windows-only functionality (by design)
- Requires internet connection for DXVK downloads
- Some antivirus software may flag DXVK DLLs
- Limited to DirectX 9/10/11 games

### Future Enhancements
- Standalone executable distribution
- Enhanced game compatibility detection
- Automatic DXVK configuration optimization
- Batch processing for multiple games
- Integration with game launchers

