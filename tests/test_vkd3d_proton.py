import io
import tarfile
from unittest.mock import patch

from github_downloader import Vkd3dProtonDownloader


def test_vkd3d_release_selects_tar_zst_asset():
    payload = {"tag_name": "v3.0.1", "assets": [{
        "name": "vkd3d-proton-3.0.1.tar.zst",
        "browser_download_url": "https://example.test/vkd3d-proton-3.0.1.tar.zst"}]}
    response = type("Response", (), {"json": lambda self: payload,
                                     "raise_for_status": lambda self: None})()
    with patch("github_downloader.requests.get", return_value=response):
        release = Vkd3dProtonDownloader().get_release_info()
    assert release["download_format"] == "tar.zst"


def test_vkd3d_mapping_and_architecture_layout():
    downloader = Vkd3dProtonDownloader()
    assert downloader.archive_subfolders == {"64-bit": "x64", "32-bit": "x86"}
    assert downloader.get_dlls("Direct3D 12") == ["d3d12.dll", "d3d12core.dll"]


def test_archive_member_matching():
    downloader = Vkd3dProtonDownloader()
    assert downloader._matches("vkd3d-proton-v3/x64/d3d12.dll", "x64", ["d3d12.dll"])
    assert not downloader._matches("vkd3d-proton-v3/x86/d3d12.dll", "x64", ["d3d12.dll"])
