#Requires -Version 5.0
<#
    DXVK Manager - Quick Installer
    Usage: irm https://raw.githubusercontent.com/xRetr000/DXVK-Manager/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$repo = "xRetr000/DXVK-Manager"
$installDir = "$env:LOCALAPPDATA\DXVKManager"

Write-Host "DXVK Manager Installer" -ForegroundColor Cyan
Write-Host "------------------------" -ForegroundColor Cyan

# 1. Get the latest release info from GitHub
Write-Host "Checking latest release..."
try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest" -Headers @{ "User-Agent" = "DXVKManager-Installer" }
} catch {
    Write-Host "Failed to reach GitHub. Check your internet connection." -ForegroundColor Red
    exit 1
}

$version = $release.tag_name
$asset = $release.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1

if (-not $asset) {
    Write-Host "No .exe asset found in the latest release." -ForegroundColor Red
    exit 1
}

Write-Host "Latest version: $version"

# 2. Create install directory
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$exePath = Join-Path $installDir $asset.name

# 3. Download the exe
Write-Host "Downloading $($asset.name)..."
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $exePath -UseBasicParsing

Write-Host "Installed to: $exePath" -ForegroundColor Green

# 4. Create a Start Menu shortcut
$startMenuPath = [Environment]::GetFolderPath("StartMenu") + "\Programs\DXVK Manager.lnk"
try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($startMenuPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $installDir
    $shortcut.IconLocation = $exePath
    $shortcut.Save()
    Write-Host "Start Menu shortcut created." -ForegroundColor Green
} catch {
    Write-Host "Could not create Start Menu shortcut (non-fatal)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! Launching DXVK Manager..." -ForegroundColor Cyan
Start-Process $exePath
