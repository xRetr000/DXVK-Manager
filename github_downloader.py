import io
import os
import tarfile
import urllib.parse
import zipfile

import requests

from constants import get_dll_map


class ArchiveDownloader:
    source_key = "official"
    source_name = "DXVK"
    dll_source = "official"
    archive_subfolders = {"64-bit": "x64", "32-bit": "x32"}

    def get_dlls(self, directx_version):
        mapping = get_dll_map(self.dll_source)
        return mapping.get(directx_version, mapping["Unknown"])

    def download_and_extract_dxvk(self, url, destination, arch, directx_version,
                                  file_format="tar.gz"):
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        subfolder = self.archive_subfolders["64-bit" if arch == "64-bit" else "32-bit"]
        dlls = self.get_dlls(directx_version)
        fmt = file_format.lower().lstrip(".")
        if fmt == "zip":
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                for name in archive.namelist():
                    if self._matches(name, subfolder, dlls):
                        with archive.open(name) as source:
                            self._write(source, destination, os.path.basename(name))
        elif fmt in ("tar.gz", "tgz", "gz"):
            with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as archive:
                self._extract_tar_members(archive, destination, subfolder, dlls)
        elif fmt in ("tar.zst", "tzst", "zst"):
            try:
                import zstandard
            except ImportError as exc:
                raise RuntimeError("Install the zstandard dependency to use vkd3d-proton.") from exc

            # Feed the compressed HTTP body directly into zstandard and tarfile.
            # This avoids materializing the decompressed tar in memory.
            response.raw.decode_content = True
            with zstandard.ZstdDecompressor().stream_reader(response.raw) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as archive:
                    self._extract_tar_members(archive, destination, subfolder, dlls)
        else:
            raise ValueError("Unsupported release archive format: " + file_format)

    @staticmethod
    def _matches(name, subfolder, dlls):
        normalized = name.replace("\\", "/").lower()
        return ("/" + subfolder.lower() + "/") in normalized and \
            os.path.basename(name).lower() in {dll.lower() for dll in dlls}

    def _extract_tar_members(self, archive, destination, subfolder, dlls):
        """Extract matching DLL members from a sequential tar stream."""
        for member in archive:
            if not member.isfile() or not self._matches(member.name, subfolder, dlls):
                continue
            source = archive.extractfile(member)
            if source:
                with source:
                    self._write(source, destination, os.path.basename(member.name))

    # Backward-compatible name for callers that used the previous helper.
    def _extract_tar(self, archive, destination, subfolder, dlls):
        self._extract_tar_members(archive, destination, subfolder, dlls)

    @staticmethod
    def _write(source, destination, filename):
        path = os.path.join(destination, filename)
        with open(path, "wb") as target:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        print("Extracted " + filename + " to " + destination)


class GithubDownloader(ArchiveDownloader):
    def __init__(self, repo_owner="doitsujin", repo_name="dxvk"):
        self.api_base_url = "https://api.github.com/repos/{}/{}".format(repo_owner, repo_name)

    def get_releases(self, limit=10):
        response = requests.get(self.api_base_url + "/releases?per_page=" + str(limit), timeout=30)
        response.raise_for_status()
        return response.json()[:limit]

    def get_release_info(self, tag_name=None):
        url = self.api_base_url + ("/releases/tags/" + tag_name if tag_name else "/releases/latest")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        asset = next((a for a in data.get("assets", [])
                      if a["name"].lower().endswith((".zip", ".tar.gz"))), None)
        if not asset:
            raise ValueError("No supported DXVK archive was found in the release.")
        data["download_url"] = asset["browser_download_url"]
        data["download_filename"] = asset["name"]
        data["download_format"] = "zip" if asset["name"].lower().endswith(".zip") else "tar.gz"
        return data

    def get_latest_release_info(self):
        return self.get_release_info()


class GitlabDownloader(ArchiveDownloader):
    source_key = "gplasync"
    source_name = "DXVK GPLAsync"

    def __init__(self):
        project = urllib.parse.quote("Ph42oN/dxvk-gplasync", safe="")
        self.api_base_url = "https://gitlab.com/api/v4/projects/" + project

    def get_releases(self, limit=10):
        response = requests.get(self.api_base_url + "/releases?per_page=" + str(limit), timeout=30)
        response.raise_for_status()
        return response.json()[:limit]

    def get_release_info(self, tag_name=None):
        releases = self.get_releases(1 if tag_name is None else 100)
        release = next((r for r in releases if tag_name is None or r["tag_name"] == tag_name), None)
        if not release:
            raise ValueError("No GPLAsync release was found.")
        return {"tag_name": release["tag_name"], "download_url": release["assets"]["links"][0]["url"],
                "download_filename": "dxvk-gplasync.tar.gz", "download_format": "tar.gz"}


class Vkd3dProtonDownloader(GithubDownloader):
    source_key = "vkd3d-proton"
    source_name = "vkd3d-proton"
    dll_source = "vkd3d-proton"
    archive_subfolders = {"64-bit": "x64", "32-bit": "x86"}

    def __init__(self):
        super().__init__("HansKristian-Work", "vkd3d-proton")

    def get_release_info(self, tag_name=None):
        url = self.api_base_url + ("/releases/tags/" + tag_name if tag_name else "/releases/latest")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        asset = next((a for a in data.get("assets", [])
                      if a["name"].lower().endswith((".tar.zst", ".tar.gz", ".zip"))), None)
        if not asset:
            raise ValueError("No supported vkd3d-proton archive was found in the release.")
        name = asset["name"].lower()
        data["download_url"] = asset["browser_download_url"]
        data["download_filename"] = asset["name"]
        data["download_format"] = "tar.zst" if name.endswith(".tar.zst") else ("zip" if name.endswith(".zip") else "tar.gz")
        return data


def get_downloader(source):
    if source == "gplasync":
        return GitlabDownloader()
    if source == "vkd3d-proton":
        return Vkd3dProtonDownloader()
    return GithubDownloader()
