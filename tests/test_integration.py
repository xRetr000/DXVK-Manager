"""
End-to-end workflow: detect → install → re-install (upgrade) → uninstall,
against a fake game folder and in-memory release archives. No network, no
changes outside the temp folder.
"""
import os
from unittest.mock import MagicMock, patch

from conftest import make_archive, make_minimal_pe
from dxvk_manager import DXVKManager
from exe_analyzer import detect_directx_version, get_exe_architecture
from logger import Logger


def _payload(sub, dll):
    return f"{sub}/{dll}".encode()


def _serve(releases_by_tag, archives_by_url):
    def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        if "api.github.com" in url:
            tag = url.rsplit("/", 1)[-1]
            resp.json = lambda: releases_by_tag["latest" if tag == "latest" else tag]
        else:
            resp.content = archives_by_url[url]
        return resp
    return patch("github_downloader.requests.get", side_effect=fake_get)


def test_full_workflow(tmp_path):
    game = str(tmp_path)
    exe = make_minimal_pe(os.path.join(game, "game.exe"), 0x14C)
    with open(os.path.join(game, "d3d11.dll"), "wb") as f:
        f.write(b"ORIGINAL")

    # Detection
    assert get_exe_architecture(exe) == "32-bit"
    assert detect_directx_version(game, exe) == ["Direct3D 11"]  # from shipped DLL

    manager = DXVKManager()
    manager.logger = Logger(str(tmp_path / "log.json"))

    dxvk_dlls = ["d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll"]
    releases = {
        "v2.6": {"tag_name": "v2.6", "assets": [{"name": "dxvk-2.6.tar.gz", "browser_download_url": "http://dl/2.6"}]},
        "latest": {"tag_name": "v2.7", "assets": [{"name": "dxvk-2.7.zip", "browser_download_url": "http://dl/2.7"}]},
    }
    archives = {
        "http://dl/2.6": make_archive("tar.gz", "dxvk-2.6", ["x32", "x64"], dxvk_dlls, lambda s, d: f"2.6 {s}/{d}".encode()),
        "http://dl/2.7": make_archive("zip", "dxvk-2.7", ["x32", "x64"], dxvk_dlls, lambda s, d: f"2.7 {s}/{d}".encode()),
    }

    with _serve(releases, archives):
        # Install a specific version
        assert manager.install_dxvk(game, "32-bit", "Direct3D 11", True, source="official", version="v2.6")
        assert open(os.path.join(game, "d3d11.dll"), "rb").read() == b"2.6 x32/d3d11.dll"
        assert open(os.path.join(game, "dxvk_backup", "d3d11.dll"), "rb").read() == b"ORIGINAL"

        # Re-detection must not be fooled by the DXVK DLL we just placed there
        assert detect_directx_version(game, exe) == ["Unknown"]

        # Upgrade to latest without uninstalling first
        assert manager.install_dxvk(game, "32-bit", "Direct3D 11", True, source="official", version=None)
        assert open(os.path.join(game, "d3d11.dll"), "rb").read() == b"2.7 x32/d3d11.dll"
        assert open(os.path.join(game, "dxvk_backup", "d3d11.dll"), "rb").read() == b"ORIGINAL"

    logs = manager.logger.get_logs()
    assert [e["dxvk_version"] for e in logs] == ["v2.6", "v2.7"]
    assert all(e["renderer"] == "DXVK" for e in logs)

    # Uninstall restores the original and removes everything we added
    assert manager.uninstall_dxvk(game)
    assert open(os.path.join(game, "d3d11.dll"), "rb").read() == b"ORIGINAL"
    assert not os.path.exists(os.path.join(game, "dxgi.dll"))
    assert not os.path.exists(os.path.join(game, "dxvk_backup"))
    assert manager.uninstall_dxvk(game) is False  # nothing left to restore
