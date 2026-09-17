import io
import os
import tarfile
import urllib.parse
import zipfile

import requests

from constants import get_dll_map


class DXVKDownloaderBase:
    """Shared release and archive extraction logic for GitHub/GitLab sources."""

    source_key = "base"
    source_name = "Base"
    archive_subfolders = {"64-bit": "x64", "32-bit": "x32"}
    dll_source = "official"

    def get_dlls(self, directx_version):
        dll_map = get_dll_map(self.dll_source)
        return dll_map.get(directx_version, dll_map.get("Unknown", []))

    def download_and_extract_dxvk(self, download_url, extract_path, arch,
                                  directx_version, file_format="tar.gz"):
        """Download a release and extract only the DLLs needed by this source."""
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
        content = response.content
        subfolder = self.archive_subfolders["64-bit" if arch == "64-bit" else "32-bit"]
        dlls_to_extract = self.get_dlls(directx_version)

        normalized_format = file_format.lower().lstrip(".")
        if normalized_format == "zip":
            self._extract_from_zip(content, extract_path, subfolder, dlls_to_extract)
        elif normalized_format in ("tar.gz", "tgz", "gz"):
            self._extract_from_targz(content, extract_path, subfolder, dlls_to_extract)
        elif normalized_format in ("tar.zst", "tzst", "zst"):
            self._extract_from_tarzst(content, extract_path, subfolder, dlls_to_extract)
        else:
            raise ValueError(f"Unsupported release archive format: {file_format}")

    @staticmethod
    def _wanted(name, dlls):
        return name.lower() in {dll.lower() for dll in dlls}

    def _write_member(self, source, extract_path, dll_name):
        target_path = os.path.join(extract_path, dll_name)
        with open(target_path, "wb") as target:
            target.write(source.read())
        print(f"Extracted {dll_name} to {extract_path}")

    def _extract_from_zip(self, content, extract_path, subfolder, dlls):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for member in archive.namelist():
                normalized = member.replace("\\", "/").lower()
                if member.endswith("/") or f"/{subfolder.lower()}/" not in normalized:
                    continue
                dll_name = os.path.basename(member)
                if self._wanted(dll_name, dlls):
                    with archive.open(member) as source:
                        self._write_member(source, extract_path, dll_name)

    def _extract_from_targz(self, content, extract_path, subfolder, dlls):
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
            self._extract_tar_members(archive, extract_path, subfolder, dlls)

    def _extract_from_tarzst(self, content, extract_path, subfolder, dlls):
        try:
            import zstandard
        except ImportError as exc:
            raise RuntimeError(
                "vkd3d-proton downloads require the zstandard package. "
                "Install the application dependencies and try again."
            ) from exc

        decompressor = zstandard.ZstdDecompressor()
        with decompressor.stream_reader(io.BytesIO(content)) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as archive:
                self._extract_tar_members(archive, extract_path, subfolder, dlls)

    def _extract_tar_members(self, archive, extract_path, subfolder, dlls):
        for member in archive:
            if not member.isfile():
                continue
            normalized = member.name.replace("\\", "/").lower()
            if f"/{subfolder.lower()}/" not in normalized:
                continue
            dll_name = os.path.basename(member.name)
            if self._wanted(dll_name, dlls):
                source = archive.extractfile(member)
                if source:
                    with source:
                        self._write_member(source, extract_path, dll_name)

    def get_version_from_url(self, download_url):
        filename = download_url.split("/")[-1]
        lower_filename = filename.lower()
        for suffix in (".tar.zst", ".tar.gz", ".zip"):
            if lower_filename.endswith(suffix):
                filename = filename[:-len(suffix)]
                break
        for prefix in ("dxvk-", "vkd3d-proton-"):
            if filename.lower().startswith(prefix):
                filename = filename[len(prefix):]
                break
        return filename

    def get_latest_release_info(self):
        return self.get_release_info(None)


class GithubDownloader(DXVKDownloaderBase):
    """Official DXVK releases from GitHub."""

    source_key = "official"
    source_name = "Official (doitsujin/dxvk)"
    dll_source = "official"

    def __init__(self, repo_owner="doitsujin", repo_name="dxvk"):
        self.api_base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    def get_releases(self, limit=10):
        response = requests.get(f"{self.api_base_url}/releases?per_page={limit}", timeout=30)
        response.raise_for_status()
        return [{"tag_name": r["tag_name"], "name": r.get("name") or r["tag_name"],
                 "published_at": r.get("published_at")} for r in response.json()[:limit]]

    def get_release_info(self, tag_name=None):
        url = f"{self.api_base_url}/releases/tags/{tag_name}" if tag_name else f"{self.api_base_url}/releases/latest"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        asset = next((a for a in data.get("assets", [])
                      if a["name"].lower().endswith((".zip", ".tar.gz"))), None)
        if not asset:
            raise ValueError("No supported ZIP or TAR.GZ asset found in this DXVK release.")
        asset_name = asset["name"].lower()
        data.update(download_url=asset["browser_download_url"], download_filename=asset["name"],
                    download_format="zip" if asset_name.endswith(".zip") else "tar.gz")
        return data


class GitlabDownloader(DXVKDownloaderBase):
    """dxvk-gplasync releases hosted on GitLab."""

    source_key = "gplasync"
    source_name = "GPLAsync (Ph42oN)"
    dll_source = "gplasync"

    def __init__(self, project_path="Ph42oN/dxvk-gplasync"):
        self.project_path = project_path
        project_id = urllib.parse.quote(project_path, safe="")
        self.api_base_url = f"https://gitlab.com/api/v4/projects/{project_id}"

    def get_releases(self, limit=10):
        response = requests.get(f"{self.api_base_url}/releases?per_page={limit}", timeout=30)
        response.raise_for_status()
        return [{"tag_name": r["tag_name"], "name": r.get("name") or r["tag_name"],
                 "published_at": r.get("released_at")} for r in response.json()[:limit]]

    def get_release_info(self, tag_name=None):
        if tag_name is None:
            releases = self.get_releases(1)
            if not releases:
                raise ValueError("No GPLAsync releases were found.")
            tag_name = releases[0]["tag_name"]
        filename = f"dxvk-gplasync-{tag_name}.tar.gz"
        return {"tag_name": tag_name, "download_url": f"https://gitlab.com/{self.project_path}/-/raw/main/releases/{filename}",
                "download_filename": filename, "download_format": "tar.gz"}


class Vkd3dProtonDownloader(GithubDownloader):
    """vkd3d-proton releases from HansKristian-Work/vkd3d-proton."""

    source_key = "vkd3d-proton"
    source_name = "vkd3d-proton (HansKristian-Work)"
    dll_source = "vkd3d-proton"
    archive_subfolders = {"64-bit": "x64", "32-bit": "x86"}

    def __init__(self):
        super().__init__("HansKristian-Work", "vkd3d-proton")

    def get_release_info(self, tag_name=None):
        url = f"{self.api_base_url}/releases/tags/{tag_name}" if tag_name else f"{self.api_base_url}/releases/latest"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        asset = next((a for a in data.get("assets", [])
                      if a["name"].lower().endswith((".tar.zst", ".tar.gz", ".zip"))), None)
        if not asset:
            raise ValueError("No supported vkd3d-proton archive asset found in this release.")
        asset_name = asset["name"].lower()
        if asset_name.endswith(".tar.zst"):
            archive_format = "tar.zst"
        elif asset_name.endswith(".tar.gz"):
            archive_format = "tar.gz"
        else:
            archive_format = "zip"
        data.update(download_url=asset["browser_download_url"], download_filename=asset["name"],
                    download_format=archive_format)
        return data

    def get_releases(self, limit=10):
        return super().get_releases(limit)


def get_downloader(source_key):
    if source_key == "gplasync":
        return GitlabDownloader()
    if source_key == "vkd3d-proton":
        return Vkd3dProtonDownloader()
    return GithubDownloader()
