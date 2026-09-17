import os
import tempfile
from unittest.mock import patch

from dxvk_manager import DXVKManager


def test_official_downloader_mock_is_preserved(tmp_path):
    manager = DXVKManager()
    game = str(tmp_path)
    fake_release = {
        "tag_name": "v-test",
        "download_url": "https://example.test/dxvk.zip",
        "download_format": "zip",
    }

    def fake_extract(url, destination, arch, directx, file_format):
        for name in ("d3d11.dll", "dxgi.dll"):
            with open(os.path.join(destination, name), "wb") as output:
                output.write(b"test")

    with patch.object(manager.downloader, "get_release_info", return_value=fake_release), \
         patch.object(manager.downloader, "download_and_extract_dxvk", side_effect=fake_extract):
        assert manager.install_dxvk(game, "64-bit", "Direct3D 11", False)

    assert os.path.isfile(os.path.join(game, "d3d11.dll"))
    assert os.path.isfile(os.path.join(game, "dxgi.dll"))
