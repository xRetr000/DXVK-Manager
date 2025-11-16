# Quick Start Guide - DXVK Manager

## 🎯 For Users (Want to Use the App?)

**Just download `DXVK_Manager.exe` and double-click it!**

That's it! No installation, no Python, no terminal needed.

---

## 🔨 For Developers (Want to Build Your Own?)

### Super Easy Method (No Terminal!)

1. **Download the source code**
2. **Double-click `BUILD.bat`**
3. **Wait 2-5 minutes** (first time takes longer)
4. **Done!** Your executable is in `dist/DXVK_Manager.exe`

**That's it!** The batch file does everything automatically.

---

## 📦 For Distribution (Want to Share It?)

### Option 1: Share the .exe Directly
- Zip `DXVK_Manager.exe` from the `dist` folder
- Share it with users
- They can extract and run it directly

### Option 2: Create an Installer (Professional)
1. Double-click `build_installer.bat`
2. Follow the prompts (if Inno Setup is installed)
3. Get a professional installer package

**See `INSTALLER_GUIDE.md` for detailed instructions**

### Option 3: Microsoft Store
- The app is ready for store submission!
- See `INSTALLER_GUIDE.md` for MSIX packaging
- Follow Microsoft Store submission guidelines

---

## ❓ Troubleshooting

### "Python is not recognized"
→ Install Python from [python.org](https://www.python.org)
→ **Important:** Check "Add Python to PATH" during installation
→ Restart your computer after installing

### Build Fails
→ Make sure you're connected to the internet
→ Try running `BUILD.bat` as Administrator
→ Check that all project files are present

### Executable Doesn't Work
→ Make sure you're using Windows 10 or 11
→ Try running as Administrator if permissions are needed
→ Check antivirus isn't blocking it (false positive)

---

## ✅ Checklist Before Distributing

- [ ] Test the .exe on a clean system (no Python installed)
- [ ] Verify all features work correctly
- [ ] Test with a real game folder
- [ ] Check file size is reasonable (20-50 MB is normal)
- [ ] Test backup and restore functionality
- [ ] Verify it works without internet (for local use)

---

## 🎁 Ready to Share!

Once you have `DXVK_Manager.exe`:
- ✅ No Python required for users
- ✅ No installation needed
- ✅ Just double-click and run
- ✅ Works on any Windows 10/11 PC
- ✅ Store-ready!

---

## 📚 Need More Help?

- **Building:** See `README_BUILD.md`
- **Creating Installer:** See `INSTALLER_GUIDE.md`
- **General Info:** See `README.md`

