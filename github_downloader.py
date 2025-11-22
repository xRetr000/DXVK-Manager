import requests
import zipfile
import tarfile
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
        
        # Find the asset - prefer .zip, fallback to .tar.gz
        # DXVK releases typically have .tar.gz files
        download_asset = None
        for asset in release_data.get('assets', []):
            asset_name = asset['name'].lower()
            if asset_name.endswith('.zip'):
                download_asset = asset
                break  # Prefer .zip if available
            elif asset_name.endswith('.tar.gz') and download_asset is None:
                download_asset = asset
        
        if not download_asset:
            # List available assets for debugging
            available_assets = [asset['name'] for asset in release_data.get('assets', [])]
            raise ValueError(
                f"No ZIP or TAR.GZ asset found in the latest DXVK release. "
                f"Available assets: {', '.join(available_assets) if available_assets else 'None'}"
            )
        
        # Add the browser_download_url to the response for convenience
        release_data['download_url'] = download_asset['browser_download_url']
        release_data['download_filename'] = download_asset['name']
        release_data['download_format'] = 'zip' if download_asset['name'].endswith('.zip') else 'tar.gz'
        return release_data

    def download_and_extract_dxvk(self, download_url, extract_path, arch, directx_version, file_format='tar.gz'):
        """Downloads the DXVK release and extracts the relevant DLLs."""
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        content = response.content
        
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
        
        # Extract based on file format
        if file_format == 'zip':
            self._extract_from_zip(content, extract_path, subfolder, dlls_to_extract)
        else:  # tar.gz
            self._extract_from_targz(content, extract_path, subfolder, dlls_to_extract)
    
    def _extract_from_zip(self, content, extract_path, subfolder, dlls_to_extract):
        """Extract DLLs from a ZIP file."""
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zip_members = zf.namelist()
            
            # Look for files in the correct architecture subfolder
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
        with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as tf:
            # Get all members
            members = tf.getmembers()
            
            # Look for files in the correct architecture subfolder
            for member in members:
                if not member.isfile():
                    continue
                
                member_path = member.name.replace('\\', '/')
                member_lower = member_path.lower()
                
                # Check if this file is in the correct architecture folder
                # DXVK structure: dxvk-x.y.z/x64/ or dxvk-x.y.z/x32/
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
        # Handle both URL and filename formats like: dxvk-x.y.z.zip or .../dxvk-x.y.z.zip
        filename = download_url.split('/')[-1]
        # Remove extensions (.zip, .tar.gz, etc.)
        name_without_ext = filename.rsplit('.', 2)[0] if '.tar.' in filename else filename.rsplit('.', 1)[0]
        # Remove 'dxvk-' prefix if present
        version = name_without_ext.replace('dxvk-', '')
        return version


