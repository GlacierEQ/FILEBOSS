# LawGlance Logo Directory

This directory contains logo files used by the LawGlance application.

## Files

- `logo.ico` - Icon file used for Windows executable
- `logo.png` - PNG version of the logo for web and UI

## Notes

If these files are missing, they will be automatically created by:
- The build script (`build_desktop_app.py`)
- The icon path fixer (`scripts/fix_icon_path.py`)

## Custom Logo

To use your own logo, replace these files with your own versions. 
Ensure that:
1. The icon file is named `logo.ico`
2. The PNG file is named `logo.png`
3. The icon has multiple sizes (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
