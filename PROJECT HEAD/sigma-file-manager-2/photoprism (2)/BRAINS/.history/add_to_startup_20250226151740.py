import os
import sys
import winreg
import shutil
from pathlib import Path

def add_to_startup():
    """Add the Sorting Hat service to Windows startup"""
    try:
        # Path to the batch file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        batch_file = os.path.join(base_dir, "run_sorting_service.bat")
        
        # Create a vbs script to run the batch file in the background
        vbs_path = os.path.join(base_dir, "start_sorting_hat_hidden.vbs")
        with open(vbs_path, 'w') as f:
            f.write(f'CreateObject("WScript.Shell").Run "{batch_file}", 0, False')
        
        # Get the startup folder path
        startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        
        # Create a shortcut to the vbs script in the startup folder
        shortcut_path = os.path.join(startup_folder, "Sorting Hat.lnk")
        
        # Create the shortcut using Windows registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SortingHat", 0, winreg.REG_SZ, f'wscript.exe "{vbs_path}"')
        winreg.CloseKey(key)
        
        print(f"✅ Sorting Hat added to startup registry!")
        return True
    except Exception as e:
        print(f"❌ Failed to add to startup: {e}")
        return False

def remove_from_startup():
    """Remove Sorting Hat from Windows startup"""
    try:
        # Remove from registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_ALL_ACCESS)
        try:
            winreg.DeleteValue(key, "SortingHat")
        except:
            pass
        winreg.CloseKey(key)
        
        # Remove VBS file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        vbs_path = os.path.join(base_dir, "start_sorting_hat_hidden.vbs")
        if os.path.exists(vbs_path):
            os.remove(vbs_path)
        
        print("✅ Sorting Hat removed from startup!")
        return True
    except Exception as e:
        print(f"❌ Failed to remove from startup: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "remove":
        remove_from_startup()
    else:
        add_to_startup()
