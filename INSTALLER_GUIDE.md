# Creating an Installer for DXVK Manager

This guide explains how to create a professional installer for distribution (including Microsoft Store).

## Quick Installer with Inno Setup (Recommended)

### Prerequisites:
1. Download [Inno Setup](https://jrsoftware.org/isdl.php) (free)
2. Install Inno Setup Compiler

### Steps:

1. **Build the executable first:**
   ```bash
   python build_executable.py
   ```

2. **Create installer script** (`installer.iss` - see below)

3. **Compile the installer:**
   - Open `installer.iss` in Inno Setup Compiler
   - Click "Build" → "Compile"
   - Your installer will be in `Output` folder

## Inno Setup Script Template

Create `installer.iss`:

```iss
[Setup]
AppName=DXVK Manager
AppVersion=1.0.0
AppPublisher=Your Name
AppPublisherURL=https://github.com/yourusername/dxvk-manager
AppSupportURL=https://github.com/yourusername/dxvk-manager
DefaultDirName={autopf}\DXVK Manager
DefaultGroupName=DXVK Manager
OutputDir=installer_output
OutputBaseFilename=DXVK_Manager_Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "dist\DXVK_Manager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\DXVK Manager"; Filename: "{app}\DXVK_Manager.exe"
Name: "{group}\{cm:UninstallProgram,DXVK Manager}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DXVK Manager"; Filename: "{app}\DXVK_Manager.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\DXVK Manager"; Filename: "{app}\DXVK_Manager.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\DXVK_Manager.exe"; Description: "{cm:LaunchProgram,DXVK Manager}"; Flags: nowait postinstall skipifsilent
```

## MSIX Package for Microsoft Store

### Using MSIX Packaging Tool:

1. **Download MSIX Packaging Tool** from Microsoft Store
2. **Create Package:**
   - File → New Package
   - Select "Application package"
   - Point to `dist\DXVK_Manager.exe`
   - Fill in package information
   - Add required capabilities
   - Build package

### Using MakeAppx (Command Line):

1. **Create manifest.xml** (see below)
2. **Create folder structure:**
   ```
   DXVKManager_1.0.0.0_x64_Test\
     DXVK_Manager.exe
     AppxManifest.xml
   ```

3. **Build package:**
   ```bash
   makeappx pack /d DXVKManager_1.0.0.0_x64_Test /p DXVKManager_1.0.0.0_x64.msix
   ```

## AppxManifest.xml Template

```xml
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="YourPublisher.DXVKManager"
            Version="1.0.0.0"
            Publisher="CN=YourPublisherName" />
  
  <Properties>
    <DisplayName>DXVK Manager</DisplayName>
    <PublisherDisplayName>Your Name</PublisherDisplayName>
    <Description>Manage DXVK installations for your games</Description>
    <Logo>Assets\Logo.png</Logo>
  </Properties>
  
  <Resources>
    <Resource Language="en-US" />
  </Resources>
  
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.19041.0" />
  </Dependencies>
  
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  
  <Applications>
    <Application Id="App" Executable="DXVK_Manager.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="DXVK Manager"
                         Description="Manage DXVK installations"
                         Square150x150Logo="Assets\Square150x150Logo.png"
                         Square44x44Logo="Assets\Square44x44Logo.png"
                         BackgroundColor="transparent">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
</Package>
```

## Auto-Build Installer Script

Create `build_installer.bat`:

```batch
@echo off
echo Building DXVK Manager Installer...
echo.

REM Build executable first
python build_executable.py
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Creating installer with Inno Setup...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    if errorlevel 1 (
        echo Installer creation failed!
        pause
        exit /b 1
    )
    echo.
    echo Installer created in installer_output folder!
) else (
    echo Inno Setup not found. Skipping installer creation.
    echo You can manually create an installer using installer.iss
)

pause
```

## Tips for Store Submission

1. **Icons**: Create 44x44, 150x150, 310x150 logo images
2. **Screenshots**: Take screenshots of the app for store listing
3. **Privacy Policy**: Create a privacy policy URL
4. **Age Rating**: Determine appropriate age rating
5. **Description**: Write clear store description
6. **Testing**: Test on clean Windows installation

## Distribution Checklist

- [ ] Build executable successfully
- [ ] Test executable on clean system
- [ ] Create installer package
- [ ] Test installer installation
- [ ] Create store assets (icons, screenshots)
- [ ] Prepare store description
- [ ] Test MSIX package (if using Store)
- [ ] Code sign the executable/installer (optional but recommended)

