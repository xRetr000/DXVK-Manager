import io
import tarfile
from unittest.mock import patch

from github_downloader import Vkd3dProtonDownloader


def test_vkd3d_release_selects_tar_zst_asset():
    downloader = Vkd3dProtonDownloader()
    payload = {
        "tag_name": "v3.0.1",
        "assets": [{
            "name": "vkd3d-proton-3.0.1.tar.zst",
            "browser_download_url": "https://example.test/vkd3d-proton-3.0.1.tar.zst",
        }],
    }
    response = type("Response", (), {
        "json": lambda self: payload,
        "raise_for_status": lambda self: None,
    })()
    with patch("github_downloader.requests.get", return_value=response):
        release = downloader.get_release_info()
    assert release["download_format"] == "tar.zst"
    assert release["download_url"].endswith(".tar.zst")


def test_vkd3d_dll_mapping_and_x86_layout():
    downloader = Vkd3dProtonDownloader()
    assert downloader.archive_subfolders["64-bit"] == "x64"
    assert downloader.archive_subfolders["32-bit"] == "x86"
    assert downloader.get_dlls("Direct3D 12") == ["d3d12.dll", "d3d12core.dll"]
