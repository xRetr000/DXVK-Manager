import requests
import zipfile
import io
import os

class GithubDownloader:
    def __init__(self, repo_owner='doitsujin', repo_name='dxvk'):
        self.api_base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    def get_latest_release_info(self):
        """Fetches information about the latest DXVK release."""
        url = f"{self.api_base_url}/releases/latest"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()

    def download_and_extract_dxvk(self, download_url, extract_path, arch, directx_version):
        """Downloads the DXVK release and extracts the relevant DLLs."""
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # Determine the correct subfolder based on architecture
            subfolder = 'x64' if arch == '64-bit' else 'x32'
            
            # Map DirectX version to DXVK DLL names
            dll_map = {
                'Direct3D 9': ['d3d9.dll', 'dxgi.dll'],
                'Direct3D 10': ['d3d10.dll', 'dxgi.dll'],
                'Direct3D 11': ['d3d11.dll', 'dxgi.dll'],
                'Unknown': ['d3d9.dll', 'd3d10.dll', 'd3d11.dll', 'dxgi.dll'] # Extract all if unknown
            }
            
            dlls_to_extract = dll_map.get(directx_version, [])

            for member in zf.namelist():
                # Construct the expected path within the zip file
                # Example: dxvk-x.y.z/x64/d3d11.dll
                expected_prefix = f"dxvk-{self.get_version_from_url(download_url)}/{subfolder}/"
                
                if member.startswith(expected_prefix):
                    dll_name = os.path.basename(member)
                    if dll_name in dlls_to_extract:
                        source = zf.open(member)
                        target_path = os.path.join(extract_path, dll_name)
                        with open(target_path, "wb") as target:
                            with source as src:
                                target.write(src.read())
                        print(f"Extracted {dll_name} to {extract_path}")

    def get_version_from_url(self, download_url):
        """Extracts the version number from the download URL."""
        # Assuming URL format like: .../dxvk-x.y.z.tar.gz or dxvk-x.y.z.zip
        filename = download_url.split('/')[-1]
        version_part = filename.split('.')[0] # dxvk-x
        return version_part.replace('dxvk-', '')


