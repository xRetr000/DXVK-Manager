# Microsoft Store Submission Guide

This guide helps you package DXVK Manager for Microsoft Store submission.

## Prerequisites

1. **Microsoft Developer Account** ($19 one-time fee or free for students)
   - Sign up at [developer.microsoft.com](https://developer.microsoft.com)

2. **Windows 10/11 SDK** (if using command line tools)
   - Download from Microsoft

3. **MSIX Packaging Tool** (optional but recommended)
   - Available in Microsoft Store

## Quick Store Packaging

### Method 1: Using MSIX Packaging Tool (Recommended)

1. **Build the executable first:**
   ```batch
   BUILD.bat
   ```

2. **Open MSIX Packaging Tool:**
   - Launch from Start menu

3. **Create Package:**
   - Choose "Application package"
   - Point to `dist\DXVK_Manager.exe`
   - Fill in package information:
     - Package name: `DXVKManager`
     - Package display name: `DXVK Manager`
     - Publisher: Your publisher name
     - Version: `1.0.0.0`
   - Add required capabilities:
     - `runFullTrust` (desktop bridge app)
   - Add logo images (see Assets section below)
   - Build package

4. **Test Package:**
   - Install the .msix file locally
   - Test all functionality
   - Verify it works correctly

### Method 2: Manual MSIX Creation

1. **Create folder structure:**
   ```
   DXVKManager_1.0.0.0_x64\
     DXVK_Manager.exe
     AppxManifest.xml
     Assets\
       Logo.png (Square 150x150)
       SmallLogo.png (44x44)
       StoreLogo.png (50x50)
   ```

2. **Create AppxManifest.xml** (see template below)

3. **Build package:**
   ```batch
   makeappx pack /d DXVKManager_1.0.0.0_x64 /p DXVKManager.msix
   ```

4. **Sign package** (required for store):
   ```batch
   signtool sign /fd sha256 /a DXVKManager.msix
   ```

## AppxManifest.xml Template

Create `AppxManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         xmlns:desktop="http://schemas.microsoft.com/appx/manifest/desktop/windows10">
  <Identity Name="YourPublisher.DXVKManager"
            Version="1.0.0.0"
            Publisher="CN=YourPublisherName"
            ProcessorArchitecture="x64" />
  
  <Properties>
    <DisplayName>DXVK Manager</DisplayName>
    <PublisherDisplayName>Your Name</PublisherDisplayName>
    <Description>Automatically install and manage DXVK (DirectX to Vulkan translation layer) for your games. DXVK can improve performance and compatibility for DirectX 9, 10, and 11 games.</Description>
    <Logo>Assets\StoreLogo.png</Logo>
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
    <Application Id="App" 
                 Executable="DXVK_Manager.exe" 
                 EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="DXVK Manager"
                         Description="Manage DXVK installations for games"
                         Square150x150Logo="Assets\Logo.png"
                         Square44x44Logo="Assets\SmallLogo.png"
                         BackgroundColor="transparent">
        <uap:DefaultTile Wide310x150Logo="Assets\WideLogo.png" />
        <uap:SplashScreen Image="Assets\SplashScreen.png" />
      </uap:VisualElements>
      
      <Extensions>
        <desktop:Extension Category="windows.fullTrustProcess" 
                          Executable="DXVK_Manager.exe" />
      </Extensions>
    </Application>
  </Applications>
</Package>
```

## Required Assets

Create these images for your store listing:

### Logo Images (in Assets folder):
- **Logo.png** - 150x150 pixels (required)
- **SmallLogo.png** - 44x44 pixels (required)
- **StoreLogo.png** - 50x50 pixels (required)
- **WideLogo.png** - 310x150 pixels (optional)
- **SplashScreen.png** - 620x300 pixels (optional)

### Store Listing Images:
- **Screenshots**: At least 1, up to 10 (1366x768 recommended)
- **Hero Art**: 1920x1080 pixels (optional)
- **Promotional Art**: 414x180 pixels (optional)

## Store Submission Checklist

### Before Submission:
- [ ] Build working executable
- [ ] Create MSIX package
- [ ] Test package installation
- [ ] Test all app functionality
- [ ] Create logo images
- [ ] Take screenshots
- [ ] Write store description
- [ ] Create privacy policy URL
- [ ] Determine age rating
- [ ] Set pricing (free or paid)

### Submission Process:
1. **Go to Partner Center:**
   - [partner.microsoft.com](https://partner.microsoft.com)
   - Sign in with developer account

2. **Create New Submission:**
   - Click "Create new app"
   - Enter app name and details

3. **Upload Package:**
   - Upload your .msix file
   - Or upload .appx/.appxbundle

4. **Fill Listing Information:**
   - App name
   - Description
   - Screenshots
   - Category
   - Age rating
   - Privacy policy URL

5. **Pricing & Availability:**
   - Set price (free or paid)
   - Choose markets
   - Set availability dates

6. **Submit for Certification:**
   - Review all information
   - Submit for Microsoft review
   - Wait 1-3 days for approval

## Store Requirements

### Technical Requirements:
- ✅ Windows 10 version 1809 (build 17763) or later
- ✅ Package must be properly signed
- ✅ Must pass Microsoft Store validation
- ✅ Must work without admin privileges (if possible)
- ✅ Must follow Windows Store policies

### Content Requirements:
- ✅ Clear app description
- ✅ Appropriate screenshots
- ✅ Privacy policy (if app collects data)
- ✅ Age rating compliance
- ✅ No copyright violations

## Tips for Approval

1. **Privacy Policy:**
   - Required if app accesses internet
   - Required if app collects any data
   - Host on GitHub Pages or similar

2. **Age Rating:**
   - Usually "E for Everyone" for utility apps
   - May be higher if app modifies system files

3. **Description:**
   - Be clear about what the app does
   - Mention system requirements
   - Include disclaimer about game compatibility

4. **Screenshots:**
   - Show actual app interface
   - Include before/after examples
   - Make them clear and professional

5. **Testing:**
   - Test on clean Windows installation
   - Test without internet (if possible)
   - Test with different game types

## Common Issues

### Rejection Reasons:

1. **Missing Privacy Policy:**
   - App accesses internet (downloads DXVK)
   - Must provide privacy policy URL

2. **Age Rating:**
   - Modifies game files
   - May require higher age rating

3. **Missing Assets:**
   - Ensure all required logo images are included
   - Check image dimensions match requirements

4. **Package Errors:**
   - Ensure package is properly signed
   - Check manifest is valid XML
   - Verify all dependencies are included

## After Approval

1. **Monitor Reviews:**
   - Respond to user feedback
   - Fix reported bugs quickly

2. **Update Regularly:**
   - Fix bugs
   - Add features
   - Keep DXVK downloads updated

3. **Marketing:**
   - Share on social media
   - Post on gaming forums
   - Create tutorial videos

## Resources

- **Partner Center:** [partner.microsoft.com](https://partner.microsoft.com)
- **Store Policies:** [docs.microsoft.com/en-us/windows/uwp/publish](https://docs.microsoft.com/en-us/windows/uwp/publish)
- **MSIX Documentation:** [docs.microsoft.com/en-us/windows/msix](https://docs.microsoft.com/en-us/windows/msix)

---

**Note:** Store submission can take 1-3 days for review. Be patient and ensure all requirements are met before submitting!

