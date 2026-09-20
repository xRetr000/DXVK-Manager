import requests
import zipfile
import tarfile
import io
import os
import urllib.parse
from constants import DLL_MAP, RENDERER_DXVK, RENDERER_VKD3D


class DXVKDownloaderBase:
    """
    Shared extraction logic for any DXVK / vkd3d-proton source (GitHub, GitLab, etc).
    Subclasses only need to implement get_releases() and get_release_info().
    """

    source_key = "base"
    source_name = "Base"
    # Which translation layer this source provides (see constants.RENDERER_*)
    renderer = RENDERER_DXVK
    # Archive subfolder holding the DLLs for each architecture
    arch_subfolders = {'64-bit': 'x64', '32-bit': 'x32'}

    def download_and_extract_dxvk(self, download_url, extract_path, arch, directx_version, file_format='tar.gz'):
        """Downloads the release archive and extracts the relevant DLLs."""
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        content = response.content

        # Determine the correct subfolder based on architecture
        subfolder = self.arch_subfolders.get(arch, self.arch_subfolders['32-bit'])

        dlls_to_extract = DLL_MAP.get(directx_version, [])

        if file_format == 'zip':
            self._extract_from_zip(content, extract_path, subfolder, dlls_to_extract)
        elif file_format == 'tar.zst':
            self._extract_from_tarzst(content, extract_path, subfolder, dlls_to_extract)
        else:  # tar.gz
            self._extract_from_targz(content, extract_path, subfolder, dlls_to_extract)

    def _extract_from_zip(self, content, extract_path, subfolder, dlls_to_extract):
        """Extract DLLs from a ZIP file."""
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zip_members = zf.namelist()

            for member in zip_members:
                if member.endswith('/'):
                    continue

                member_lower = member.lower().replace('\\', '/')
                if f'/{subfolder.lower()}/' in member_lower or f'\\{subfolder.lower()}\\' in member_lower:
                    dll_name = os.path.basename(member)
                    if dll_name.lower() in [d.lower() for d in dlls_to_extract]:
                        try:
                            source = zf.open(member)
                            target_path = os.path.join(extract_path, dll_name)
                            with open(target_path, "wb") as target:
                                target.write(source.read())
                            source.close()
                            print(f"Extracted {dll_name} to {extract_path}")
                        except Exception as e:
                            print(f"Error extracting {dll_name}: {e}")

    def _extract_from_targz(self, content, extract_path, subfolder, dlls_to_extract):
        """Extract DLLs from a TAR.GZ file."""
        self._extract_from_tar(io.BytesIO(content), 'r:gz', extract_path, subfolder, dlls_to_extract)

    def _extract_from_tarzst(self, content, extract_path, subfolder, dlls_to_extract):
        """Extract DLLs from a TAR.ZST (Zstandard-compressed tar) file, as shipped by vkd3d-proton."""
        try:
            import zstandard
        except ImportError:
            raise ImportError(
                "The 'zstandard' package is required to extract .tar.zst archives. "
                "Install it with: pip install zstandard"
            )

        # tarfile has no native zstd support, so decompress to an in-memory tar first
        decompressed = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(content)).read()
        self._extract_from_tar(io.BytesIO(decompressed), 'r:', extract_path, subfolder, dlls_to_extract)

    def _extract_from_tar(self, fileobj, mode, extract_path, subfolder, dlls_to_extract):
        """Extract DLLs from an open tar stream (any compression tarfile understands)."""
        with tarfile.open(fileobj=fileobj, mode=mode) as tf:
            members = tf.getmembers()

            for member in members:
                if not member.isfile():
                    continue

                member_path = member.name.replace('\\', '/')
                member_lower = member_path.lower()

                # DXVK structure: dxvk-x.y.z/x64/ or dxvk-x.y.z/x32/
                # vkd3d-proton structure: vkd3d-proton-x.y.z/x64/ or vkd3d-proton-x.y.z/x86/
                if f'/{subfolder.lower()}/' in member_lower:
                    dll_name = os.path.basename(member.name)
                    if dll_name.lower() in [d.lower() for d in dlls_to_extract]:
                        try:
                            source = tf.extractfile(member)
                            if source:
                                target_path = os.path.join(extract_path, dll_name)
                                with open(target_path, "wb") as target:
                                    target.write(source.read())
                                source.close()
                                print(f"Extracted {dll_name} to {extract_path}")
                        except Exception as e:
                            print(f"Error extracting {dll_name}: {e}")

    def get_version_from_url(self, download_url):
        """Extracts the version number from the download URL or filename."""
        filename = download_url.split('/')[-1]
        name_without_ext = filename.rsplit('.', 2)[0] if '.tar.' in filename else filename.rsplit('.', 1)[0]
        version = name_without_ext.replace('vkd3d-proton-', '').replace('dxvk-', '')
        return version

    # Backward-compatible alias used by older callers
    def get_latest_release_info(self):
        return self.get_release_info(None)


class GithubDownloader(DXVKDownloaderBase):
    """Official DXVK releases from GitHub (doitsujin/dxvk)."""

    source_key = "official"
    source_name = "Official (doitsujin/dxvk)"

    def __init__(self, repo_owner='doitsujin', repo_name='dxvk'):
        self.api_base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    def get_releases(self, limit=10):
        """Returns the most recent releases as a list of {tag_name, name, published_at}."""
        url = f"{self.api_base_url}/releases?per_page={limit}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        releases = response.json()
        return [
            {
                "tag_name": r["tag_name"],
                "name": r.get("name") or r["tag_name"],
                "published_at": r.get("published_at"),
            }
            for r in releases[:limit]
        ]

    def get_release_info(self, tag_name=None):
        """Fetches a specific release by tag, or the latest if tag_name is None."""
        if tag_name:
            url = f"{self.api_base_url}/releases/tags/{tag_name}"
        else:
            url = f"{self.api_base_url}/releases/latest"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        release_data = response.json()

        # Find the asset - prefer .zip, fallback to .tar.gz
        download_asset = None
        for asset in release_data.get('assets', []):
            asset_name = asset['name'].lower()
            if asset_name.endswith('.zip'):
                download_asset = asset
                break
            elif asset_name.endswith('.tar.gz') and download_asset is None:
                download_asset = asset

        if not download_asset:
            available_assets = [asset['name'] for asset in release_data.get('assets', [])]
            raise ValueError(
                f"No ZIP or TAR.GZ asset found in this DXVK release. "
                f"Available assets: {', '.join(available_assets) if available_assets else 'None'}"
            )

        release_data['download_url'] = download_asset['browser_download_url']
        release_data['download_filename'] = download_asset['name']
        release_data['download_format'] = 'zip' if download_asset['name'].endswith('.zip') else 'tar.gz'
        return release_data


class GitlabDownloader(DXVKDownloaderBase):
    """
    dxvk-gplasync releases, hosted on GitLab (Ph42oN/dxvk-gplasync) rather than GitHub.
    Release assets are stored in-repo under releases/dxvk-gplasync-{tag}.tar.gz,
    referenced via GitLab's raw file URLs.
    """

    source_key = "gplasync"
    source_name = "GPLAsync (Ph42oN)"

    def __init__(self, project_path='Ph42oN/dxvk-gplasync'):
        self.project_path = project_path
        project_id = urllib.parse.quote(project_path, safe='')
        self.api_base_url = f"https://gitlab.com/api/v4/projects/{project_id}"

    def get_releases(self, limit=10):
        """Returns the most recent releases as a list of {tag_name, name, published_at}."""
        url = f"{self.api_base_url}/releases?per_page={limit}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        releases = response.json()
        return [
            {
                "tag_name": r["tag_name"],
                "name": r.get("name") or r["tag_name"],
                "published_at": r.get("released_at"),
            }
            for r in releases[:limit]
        ]

    def get_release_info(self, tag_name=None):
        """Builds release info for a specific tag, or the most recent if tag_name is None."""
        if tag_name is None:
            releases = self.get_releases(limit=1)
            if not releases:
                raise ValueError("No GPLAsync releases were found.")
            tag_name = releases[0]["tag_name"]

        filename = f"dxvk-gplasync-{tag_name}.tar.gz"
        download_url = f"https://gitlab.com/{self.project_path}/-/raw/main/releases/{filename}"

        return {
            "tag_name": tag_name,
            "download_url": download_url,
            "download_filename": filename,
            "download_format": "tar.gz",
        }


class Vkd3dDownloader(DXVKDownloaderBase):
    """
    vkd3d-proton releases from GitHub (HansKristian-Work/vkd3d-proton).
    Provides D3D12 → Vulkan translation, which DXVK does not cover.
    Releases ship as a single .tar.zst archive containing x64/ and x86/ folders.
    """

    source_key = "vkd3d-proton"
    source_name = "Official (HansKristian-Work/vkd3d-proton)"
    renderer = RENDERER_VKD3D
    arch_subfolders = {'64-bit': 'x64', '32-bit': 'x86'}

    def __init__(self, repo_owner='HansKristian-Work', repo_name='vkd3d-proton'):
        self.api_base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    def get_releases(self, limit=10):
        """Returns the most recent releases as a list of {tag_name, name, published_at}."""
        url = f"{self.api_base_url}/releases?per_page={limit}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        releases = response.json()
        return [
            {
                "tag_name": r["tag_name"],
                "name": r.get("name") or r["tag_name"],
                "published_at": r.get("published_at"),
            }
            for r in releases[:limit]
        ]

    def get_release_info(self, tag_name=None):
        """Fetches a specific release by tag, or the latest if tag_name is None."""
        if tag_name:
            url = f"{self.api_base_url}/releases/tags/{tag_name}"
        else:
            url = f"{self.api_base_url}/releases/latest"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        release_data = response.json()

        # vkd3d-proton only publishes .tar.zst, but accept .tar.gz / .zip in case that changes
        download_asset = None
        download_format = None
        for asset in release_data.get('assets', []):
            asset_name = asset['name'].lower()
            if asset_name.endswith('.tar.zst'):
                download_asset, download_format = asset, 'tar.zst'
                break
            elif asset_name.endswith('.tar.gz') and download_asset is None:
                download_asset, download_format = asset, 'tar.gz'
            elif asset_name.endswith('.zip') and download_asset is None:
                download_asset, download_format = asset, 'zip'

        if not download_asset:
            available_assets = [asset['name'] for asset in release_data.get('assets', [])]
            raise ValueError(
                f"No TAR.ZST, TAR.GZ or ZIP asset found in this vkd3d-proton release. "
                f"Available assets: {', '.join(available_assets) if available_assets else 'None'}"
            )

        release_data['download_url'] = download_asset['browser_download_url']
        release_data['download_filename'] = download_asset['name']
        release_data['download_format'] = download_format
        return release_data


# All available sources, keyed by source_key
DOWNLOADERS = {
    GithubDownloader.source_key: GithubDownloader,
    GitlabDownloader.source_key: GitlabDownloader,
    Vkd3dDownloader.source_key: Vkd3dDownloader,
}


def get_downloader(source_key):
    """Factory: returns the appropriate downloader instance for a source key."""
    downloader_cls = DOWNLOADERS.get(source_key, GithubDownloader)
    return downloader_cls()


def get_sources_for_renderer(renderer):
    """Returns [(source_key, source_name)] for every source that provides the given renderer."""
    return [
        (cls.source_key, cls.source_name)
        for cls in DOWNLOADERS.values()
        if cls.renderer == renderer
    ]