import os
from unittest.mock import patch

import pytest

from conftest import make_archive
from dxvk_manager import DXVKManager
from logger import Logger


def _payload(sub, dll):
    return f"{sub}/{dll}".encode()


@pytest.fixture
def manager(tmp_path):
    m = DXVKManager()
    m.logger = Logger(str(tmp_path / "log.json"))  # keep the real log file untouched
    return m


def _serve(archive_bytes, release):
    """Patch the network so release lookup and download both come from memory."""
    from unittest.mock import MagicMock

    def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        if "api.github.com" in url or "gitlab.com/api" in url:
            resp.json = lambda: release
        else:
            resp.content = archive_bytes
        return resp
    return patch("github_downloader.requests.get", side_effect=fake_get)


def test_install_dxvk_then_uninstall(manager, game_dir):
    with open(os.path.join(game_dir, "d3d11.dll"), "wb") as f:
        f.write(b"ORIGINAL")
    archive = make_archive("zip", "dxvk-2.7", ["x32", "x64"],
                           ["d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll"], _payload)
    release = {"tag_name": "v2.7", "assets": [{"name": "dxvk-2.7.zip", "browser_download_url": "http://dl/dxvk-2.7.zip"}]}

    with _serve(archive, release):
        assert manager.install_dxvk(game_dir, "64-bit", "Direct3D 11", True, source="official", version="v2.7")

    assert open(os.path.join(game_dir, "d3d11.dll"), "rb").read() == _payload("x64", "d3d11.dll")
    assert os.path.exists(os.path.join(game_dir, "dxgi.dll"))
    assert not os.path.exists(os.path.join(game_dir, "d3d9.dll"))
    entry = manager.logger.get_logs()[-1]
    assert entry["renderer"] == "DXVK" and entry["dxvk_version"] == "v2.7" and entry["directx_version"] == "Direct3D 11"

    assert manager.uninstall_dxvk(game_dir)
    assert open(os.path.join(game_dir, "d3d11.dll"), "rb").read() == b"ORIGINAL"
    assert not os.path.exists(os.path.join(game_dir, "dxgi.dll"))


def test_install_vkd3d_proton_32bit(manager, game_dir):
    archive = make_archive("tar.zst", "vkd3d-proton-3.0.1", ["x86", "x64"], ["d3d12.dll", "d3d12core.dll"], _payload)
    release = {"tag_name": "v3.0.1", "assets": [{"name": "vkd3d-proton-3.0.1.tar.zst", "browser_download_url": "http://dl/v.tar.zst"}]}

    with _serve(archive, release):
        assert manager.install_dxvk(game_dir, "32-bit", "Direct3D 12", True, source="vkd3d-proton")

    assert open(os.path.join(game_dir, "d3d12.dll"), "rb").read() == _payload("x86", "d3d12.dll")
    assert open(os.path.join(game_dir, "d3d12core.dll"), "rb").read() == _payload("x86", "d3d12core.dll")
    assert not os.path.exists(os.path.join(game_dir, "dxgi.dll"))
    assert manager.logger.get_logs()[-1]["renderer"] == "vkd3d-proton"


@pytest.mark.parametrize("source,directx", [
    ("vkd3d-proton", "Direct3D 11"),
    ("vkd3d-proton", "Direct3D 9"),
    ("vkd3d-proton", "Unknown"),
    ("official", "Direct3D 12"),
    ("gplasync", "Direct3D 12"),
])
def test_renderer_directx_mismatch_is_rejected_offline(manager, game_dir, source, directx):
    with patch("github_downloader.requests.get") as get:
        assert manager.install_dxvk(game_dir, "64-bit", directx, True, source=source) is False
        assert get.call_count == 0, "mismatch must be rejected before any network call"


def test_bad_architecture_is_rejected(manager, game_dir):
    with patch("github_downloader.requests.get") as get:
        assert manager.install_dxvk(game_dir, "Not detected", "Direct3D 11", True) is False
        assert get.call_count == 0


def test_missing_folder_is_rejected(manager, tmp_path):
    assert manager.install_dxvk(str(tmp_path / "nope"), "64-bit", "Direct3D 11", True) is False


def test_archive_without_needed_dlls_fails(manager, game_dir):
    archive = make_archive("zip", "dxvk-2.7", ["x64"], ["d3d9.dll"], _payload)  # no d3d11
    release = {"tag_name": "v2.7", "assets": [{"name": "dxvk-2.7.zip", "browser_download_url": "http://dl/d.zip"}]}
    with _serve(archive, release):
        assert manager.install_dxvk(game_dir, "64-bit", "Direct3D 11", True) is False
    assert not os.path.exists(os.path.join(game_dir, "d3d11.dll"))
