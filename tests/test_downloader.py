import os
from unittest.mock import MagicMock, patch

import pytest

from conftest import make_archive
from constants import RENDERER_DXVK, RENDERER_VKD3D
from github_downloader import (
    GithubDownloader, GitlabDownloader, Vkd3dDownloader,
    get_downloader, get_sources_for_renderer,
)


def _payload(sub, dll):
    return f"{sub}/{dll}".encode()


def _fake_response(content):
    resp = MagicMock()
    resp.content = content
    resp.raise_for_status = lambda: None
    return resp


# ── factory / registry ────────────────────────────────────────────────

def test_get_downloader_routes_by_source_key():
    assert isinstance(get_downloader("official"), GithubDownloader)
    assert isinstance(get_downloader("gplasync"), GitlabDownloader)
    assert isinstance(get_downloader("vkd3d-proton"), Vkd3dDownloader)
    assert isinstance(get_downloader("nonsense"), GithubDownloader)


def test_sources_for_renderer():
    assert [k for k, _ in get_sources_for_renderer(RENDERER_DXVK)] == ["official", "gplasync"]
    assert [k for k, _ in get_sources_for_renderer(RENDERER_VKD3D)] == ["vkd3d-proton"]


def test_renderer_and_subfolders():
    assert GithubDownloader.renderer == RENDERER_DXVK
    assert GitlabDownloader.renderer == RENDERER_DXVK
    assert Vkd3dDownloader.renderer == RENDERER_VKD3D
    assert GithubDownloader.arch_subfolders["32-bit"] == "x32"
    assert Vkd3dDownloader.arch_subfolders["32-bit"] == "x86"


# ── extraction ────────────────────────────────────────────────────────

@pytest.mark.parametrize("fmt", ["zip", "tar.gz"])
@pytest.mark.parametrize("arch,sub", [("64-bit", "x64"), ("32-bit", "x32")])
def test_dxvk_extracts_only_requested_dlls_for_arch(tmp_path, fmt, arch, sub):
    archive = make_archive(fmt, "dxvk-2.7", ["x32", "x64"],
                           ["d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll"], _payload)
    with patch("github_downloader.requests.get", return_value=_fake_response(archive)):
        GithubDownloader().download_and_extract_dxvk("http://x/dxvk.zip", str(tmp_path), arch, "Direct3D 11", fmt)

    assert sorted(os.listdir(tmp_path)) == ["d3d11.dll", "dxgi.dll"]
    assert (tmp_path / "d3d11.dll").read_bytes() == _payload(sub, "d3d11.dll")


@pytest.mark.parametrize("arch,sub", [("64-bit", "x64"), ("32-bit", "x86")])
def test_vkd3d_extracts_from_tar_zst(tmp_path, arch, sub):
    archive = make_archive("tar.zst", "vkd3d-proton-3.0.1", ["x86", "x64"],
                           ["d3d12.dll", "d3d12core.dll"], _payload)
    with patch("github_downloader.requests.get", return_value=_fake_response(archive)):
        Vkd3dDownloader().download_and_extract_dxvk("http://x/v.tar.zst", str(tmp_path), arch, "Direct3D 12", "tar.zst")

    assert sorted(os.listdir(tmp_path)) == ["d3d12.dll", "d3d12core.dll"]
    assert (tmp_path / "d3d12core.dll").read_bytes() == _payload(sub, "d3d12core.dll")


def test_unknown_directx_extracts_all_dxvk_dlls(tmp_path):
    archive = make_archive("tar.gz", "dxvk-2.7", ["x64"],
                           ["d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll"], _payload)
    with patch("github_downloader.requests.get", return_value=_fake_response(archive)):
        GithubDownloader().download_and_extract_dxvk("http://x/dxvk.tar.gz", str(tmp_path), "64-bit", "Unknown", "tar.gz")
    assert sorted(os.listdir(tmp_path)) == ["d3d10core.dll", "d3d11.dll", "d3d9.dll", "dxgi.dll"]


def test_archive_paths_cannot_escape_extract_dir(tmp_path):
    """Members with traversal paths are written by basename only."""
    import io, tarfile, gzip
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        data = b"evil"
        info = tarfile.TarInfo("dxvk-2.7/x64/../../../d3d11.dll")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    archive = gzip.compress(buf.getvalue())
    with patch("github_downloader.requests.get", return_value=_fake_response(archive)):
        GithubDownloader().download_and_extract_dxvk("http://x/dxvk.tar.gz", str(tmp_path), "64-bit", "Direct3D 11", "tar.gz")
    assert os.listdir(tmp_path) == ["d3d11.dll"]
    assert not os.path.exists(tmp_path.parent.parent / "d3d11.dll")


# ── release metadata ──────────────────────────────────────────────────

def _json_response(payload):
    resp = MagicMock()
    resp.json = lambda: payload
    resp.raise_for_status = lambda: None
    return resp


def test_github_prefers_zip_over_targz():
    payload = {"tag_name": "v2.7", "assets": [
        {"name": "dxvk-2.7.tar.gz", "browser_download_url": "u/tgz"},
        {"name": "dxvk-2.7.zip", "browser_download_url": "u/zip"},
    ]}
    with patch("github_downloader.requests.get", return_value=_json_response(payload)):
        info = GithubDownloader().get_release_info("v2.7")
    assert info["download_format"] == "zip" and info["download_url"] == "u/zip"


def test_vkd3d_selects_tar_zst_asset():
    payload = {"tag_name": "v3.0.1", "assets": [
        {"name": "vkd3d-proton-3.0.1.tar.zst", "browser_download_url": "u/zst"},
    ]}
    with patch("github_downloader.requests.get", return_value=_json_response(payload)):
        info = Vkd3dDownloader().get_release_info()
    assert info["download_format"] == "tar.zst" and info["download_url"] == "u/zst"


def test_vkd3d_raises_when_no_supported_asset():
    payload = {"tag_name": "v3", "assets": [{"name": "notes.txt", "browser_download_url": "u"}]}
    with patch("github_downloader.requests.get", return_value=_json_response(payload)):
        with pytest.raises(ValueError, match="notes.txt"):
            Vkd3dDownloader().get_release_info()


def test_gitlab_release_info_builds_raw_url():
    info = GitlabDownloader().get_release_info("v2.7-1")
    assert info["download_format"] == "tar.gz"
    assert info["download_url"].endswith("/releases/dxvk-gplasync-v2.7-1.tar.gz")


def test_get_version_from_url():
    d = GithubDownloader()
    assert d.get_version_from_url("https://x/dxvk-2.7.1.tar.gz") == "2.7.1"
    assert d.get_version_from_url("https://x/dxvk-2.7.1.zip") == "2.7.1"
    assert d.get_version_from_url("https://x/vkd3d-proton-3.0.1.tar.zst") == "3.0.1"
