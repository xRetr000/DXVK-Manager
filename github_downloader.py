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
        release_data = response.json()
        
        # Find the ZIP asset (DXVK releases typically have a .tar.gz and .zip file)
        # Prefer .zip file for easier extraction
        zip_asset = None
        for asset in release_data.get('assets', []):
            if asset['name'].endswith('.zip'):
                zip_asset = asset
                break
        
        if not zip_asset:
            raise ValueError("No ZIP asset found in the latest DXVK release")
        
        # Add the browser_download_url to the response for convenience
        release_data['download_url'] = zip_asset['browser_download_url']
        release_data['download_filename'] = zip_asset['name']
        return release_data

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

            # DXVK release ZIP structure: dxvk-x.y.z/x64/ or dxvk-x.y.z/x32/
            # Find the correct folder (x64 or x32) in the ZIP
            zip_members = zf.namelist()
            
            # Look for files in the correct architecture subfolder
            # Example paths: "dxvk-2.3/x64/d3d11.dll" or "dxvk-2.3/x32/d3d11.dll"
            for member in zip_members:
                # Skip directories
                if member.endswith('/'):
                    continue
                    
                # Check if this file is in the correct architecture folder
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

    def get_version_from_url(self, download_url):
        """Extracts the version number from the download URL or filename."""
        # Handle both URL and filename formats like: dxvk-x.y.z.zip or .../dxvk-x.y.z.zip
        filename = download_url.split('/')[-1]
        # Remove extensions (.zip, .tar.gz, etc.)
        name_without_ext = filename.rsplit('.', 2)[0] if '.tar.' in filename else filename.rsplit('.', 1)[0]
        # Remove 'dxvk-' prefix if present
        version = name_without_ext.replace('dxvk-', '')
        return version


