import os
from unittest.mock import patch

from conftest import make_minimal_pe
from exe_analyzer import (
    detect_directx_details, detect_directx_version, get_best_exe,
    get_exe_architecture, get_exe_files, get_pe_imports,
)


def _touch(path, data=b""):
    with open(path, "wb") as f:
        f.write(data)


def test_get_exe_architecture(tmp_path):
    assert get_exe_architecture(make_minimal_pe(str(tmp_path / "a.exe"), 0x8664)) == "64-bit"
    assert get_exe_architecture(make_minimal_pe(str(tmp_path / "b.exe"), 0x14C)) == "32-bit"
    _touch(str(tmp_path / "junk.exe"), b"MZ" + b"\0" * 100)
    assert get_exe_architecture(str(tmp_path / "junk.exe")) == "Not a valid PE file"
    assert get_exe_architecture(str(tmp_path / "missing.exe")) == "File not found"


def test_get_exe_files_and_best_exe(tmp_path):
    _touch(str(tmp_path / "small.exe"), b"x")
    _touch(str(tmp_path / "Game.EXE"), b"x" * 100)
    _touch(str(tmp_path / "readme.txt"))
    assert sorted(get_exe_files(str(tmp_path))) == ["Game.EXE", "small.exe"]
    assert get_best_exe(str(tmp_path)) == str(tmp_path / "Game.EXE")
    assert get_best_exe(str(tmp_path / "empty")) is None


def test_get_pe_imports_on_invalid_file_is_empty(tmp_path):
    _touch(str(tmp_path / "x.exe"), b"not a pe")
    assert get_pe_imports(str(tmp_path / "x.exe")) == set()


def test_detects_from_exe_imports(tmp_path):
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    with patch("exe_analyzer.get_pe_imports", return_value={"kernel32.dll", "d3d11.dll", "dxgi.dll"}):
        info = detect_directx_details(str(tmp_path), exe)
    assert info == {"versions": ["Direct3D 11"], "method": "exe imports"}


def test_detects_from_engine_dll_imports(tmp_path):
    """Unity-style: the .exe imports nothing, UnityPlayer.dll imports d3d11."""
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    _touch(str(tmp_path / "UnityPlayer.dll"), b"x" * 1000)
    _touch(str(tmp_path / "steam_api64.dll"), b"x" * 10)

    def fake_imports(path):
        return {"d3d11.dll", "dxgi.dll"} if path.endswith("UnityPlayer.dll") else set()

    with patch("exe_analyzer.get_pe_imports", side_effect=fake_imports):
        info = detect_directx_details(str(tmp_path), exe)
    assert info == {"versions": ["Direct3D 11"], "method": "UnityPlayer.dll imports"}


def test_detects_d3d12_from_imports(tmp_path):
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    with patch("exe_analyzer.get_pe_imports", return_value={"d3d12.dll"}):
        assert detect_directx_version(str(tmp_path), exe) == ["Direct3D 12"]


def test_multiple_apis_reported_in_stable_order(tmp_path):
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    with patch("exe_analyzer.get_pe_imports", return_value={"d3d12.dll", "d3d11.dll", "d3d9.dll"}):
        assert detect_directx_version(str(tmp_path), exe) == ["Direct3D 9", "Direct3D 11", "Direct3D 12"]


def test_falls_back_to_shipped_dlls(tmp_path):
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    _touch(str(tmp_path / "d3d9.dll"))
    with patch("exe_analyzer.get_pe_imports", return_value=set()):
        info = detect_directx_details(str(tmp_path), exe)
    assert info == {"versions": ["Direct3D 9"], "method": "DLLs in game folder"}


def test_ignores_dlls_installed_by_dxvk_manager(tmp_path):
    """After a DXVK install the folder contains our d3d11.dll — that's not evidence about the game."""
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    os.makedirs(tmp_path / "dxvk_backup")
    (tmp_path / "dxvk_backup" / "installed_dlls.txt").write_text("d3d11.dll\ndxgi.dll\n")
    _touch(str(tmp_path / "d3d11.dll"))
    _touch(str(tmp_path / "dxgi.dll"))
    with patch("exe_analyzer.get_pe_imports", return_value=set()):
        assert detect_directx_version(str(tmp_path), exe) == ["Unknown"]


def test_falls_back_to_string_scan(tmp_path):
    exe = str(tmp_path / "game.exe")
    _touch(exe, b"\0" * 64 + b"LoadLibraryA" + b"d3d12.dll" + b"\0" * 64)  # not a valid PE
    info = detect_directx_details(str(tmp_path), exe)
    assert info["versions"] == ["Direct3D 12"]
    assert info["method"].startswith("strings in exe")


def test_string_scan_finds_utf16(tmp_path):
    exe = str(tmp_path / "game.exe")
    _touch(exe, b"\0" * 8 + "d3d11.dll".encode("utf-16le") + b"\0" * 8)
    assert detect_directx_version(str(tmp_path), exe) == ["Direct3D 11"]


def test_unknown_when_nothing_found(tmp_path):
    exe = make_minimal_pe(str(tmp_path / "game.exe"))
    with patch("exe_analyzer.get_pe_imports", return_value=set()):
        assert detect_directx_details(str(tmp_path), exe) == {"versions": ["Unknown"], "method": "none"}


def test_exe_path_defaults_to_best_exe(tmp_path):
    make_minimal_pe(str(tmp_path / "launcher.exe"))
    big = make_minimal_pe(str(tmp_path / "game.exe"))
    with open(big, "ab") as f:
        f.write(b"\0" * 4096)
    seen = []

    def fake_imports(path):
        seen.append(os.path.basename(path))
        return {"d3d11.dll"}

    with patch("exe_analyzer.get_pe_imports", side_effect=fake_imports):
        detect_directx_version(str(tmp_path))
    assert seen[0] == "game.exe"
