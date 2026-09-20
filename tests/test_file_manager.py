import os

import pytest

from file_manager import FileManager, MANIFEST_FILE


def _write(path, text):
    with open(path, "w") as f:
        f.write(text)


def _read(path):
    with open(path) as f:
        return f.read()


@pytest.fixture
def fm():
    return FileManager()


def test_backup_and_restore_roundtrip(fm, tmp_path):
    game = str(tmp_path)
    _write(os.path.join(game, "d3d11.dll"), "ORIGINAL")

    fm.backup_dlls(game, ["d3d11.dll", "dxgi.dll"])
    _write(os.path.join(game, "d3d11.dll"), "DXVK")
    _write(os.path.join(game, "dxgi.dll"), "DXVK")

    assert fm.restore_dlls(game) is True
    assert _read(os.path.join(game, "d3d11.dll")) == "ORIGINAL"
    assert not os.path.exists(os.path.join(game, "dxgi.dll")), "DLL the game never had must be removed"
    assert not os.path.exists(os.path.join(game, "dxvk_backup"))


def test_reinstall_keeps_original_backup(fm, tmp_path):
    """Upgrading DXVK without uninstalling first must not clobber the original DLL backup."""
    game = str(tmp_path)
    dll = os.path.join(game, "d3d11.dll")
    _write(dll, "ORIGINAL")

    fm.backup_dlls(game, ["d3d11.dll"])
    _write(dll, "DXVK v1")
    fm.backup_dlls(game, ["d3d11.dll"])  # second install, folder now holds our DLL
    _write(dll, "DXVK v2")

    assert _read(os.path.join(game, "dxvk_backup", "d3d11.dll")) == "ORIGINAL"
    fm.restore_dlls(game)
    assert _read(dll) == "ORIGINAL"


def test_manifest_merges_across_installs(fm, tmp_path):
    """Installing vkd3d-proton next to DXVK must record both sets so uninstall removes both."""
    game = str(tmp_path)
    fm.backup_dlls(game, ["d3d11.dll", "dxgi.dll"])
    _write(os.path.join(game, "d3d11.dll"), "DXVK")
    _write(os.path.join(game, "dxgi.dll"), "DXVK")

    fm.backup_dlls(game, ["d3d12.dll", "d3d12core.dll"])
    _write(os.path.join(game, "d3d12.dll"), "VKD3D")
    _write(os.path.join(game, "d3d12core.dll"), "VKD3D")

    assert fm.read_manifest(game) == ["d3d11.dll", "dxgi.dll", "d3d12.dll", "d3d12core.dll"]
    assert fm.restore_dlls(game) is True
    for name in ("d3d11.dll", "dxgi.dll", "d3d12.dll", "d3d12core.dll"):
        assert not os.path.exists(os.path.join(game, name)), name


def test_dll_we_installed_is_never_backed_up(fm, tmp_path):
    """If the manifest says we installed d3d11.dll, a later backup must not treat it as an original."""
    game = str(tmp_path)
    fm.backup_dlls(game, ["d3d11.dll"])          # game had no d3d11.dll → nothing backed up
    _write(os.path.join(game, "d3d11.dll"), "DXVK")
    backed_up = fm.backup_dlls(game, ["d3d11.dll"])
    assert backed_up == []
    assert not os.path.exists(os.path.join(game, "dxvk_backup", "d3d11.dll"))


def test_copy_dlls(fm, tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    _write(str(src / "d3d11.dll"), "DXVK")
    copied = fm.copy_dlls(str(src), str(dst), ["d3d11.dll", "missing.dll"])
    assert copied == ["d3d11.dll"]
    assert _read(str(dst / "d3d11.dll")) == "DXVK"


def test_copy_dlls_unwritable_folder_raises(fm, tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    _write(str(src / "d3d11.dll"), "DXVK")
    monkeypatch.setattr(FileManager, "can_write_to", staticmethod(lambda d: False))
    with pytest.raises(PermissionError):
        fm.copy_dlls(str(src), str(tmp_path), ["d3d11.dll"])


def test_can_write_to(fm, tmp_path):
    assert fm.can_write_to(str(tmp_path)) is True
    assert fm.can_write_to(str(tmp_path / "does-not-exist")) is False
    assert os.listdir(tmp_path) == [], "probe file must be cleaned up"


def test_is_under_program_files(fm, monkeypatch):
    monkeypatch.setenv("ProgramFiles", r"C:\Program Files")
    monkeypatch.setenv("ProgramFiles(x86)", r"C:\Program Files (x86)")
    monkeypatch.setenv("ProgramW6432", r"C:\Program Files")
    assert fm._is_under_program_files(r"c:\program files (x86)\Steam\steamapps\common\Game")
    assert fm._is_under_program_files(r"C:\Program Files\Game")
    assert not fm._is_under_program_files(r"C:\Program Filesystem\Game")
    assert not fm._is_under_program_files(r"D:\Games\Game")


def test_restore_without_backup_returns_false(fm, tmp_path):
    assert fm.restore_dlls(str(tmp_path)) is False
