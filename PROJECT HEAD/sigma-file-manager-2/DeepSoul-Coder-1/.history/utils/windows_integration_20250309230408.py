"""
Windows Integration - Utilities for deep integration with Windows OS
"""
import os
import sys
import logging
import winreg
import ctypes
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

# Import Windows-specific libraries if available
try:
    import win32api
    import win32con
    import win32gui
    import win32com.client
    from win32com.shell import shell, shellcon
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logging.warning("Windows integration features limited: win32 libraries not installed")

logger = logging.getLogger("DeepSoul-WindowsIntegration")

# Application constants
APP_NAME = "DeepSeek-Coder"
APP_ID = "DeepSeek.Coder.1"  # Application User Model ID for Windows

class WindowsIntegration:
    """Utilities for deep integration with Windows OS"""
    
    def __init__(self, app_path: str):
        """
        Initialize Windows integration
        
        Args:
            app_path: Path to the main application executable
        """
        self.app_path = os.path.abspath(app_path)
        self.app_dir = os.path.dirname(self.app_path)
        
        # Check if running on Windows
        self.is_windows = sys.platform.startswith('win')
        if not self.is_windows:
            logger.warning("Windows integration not available on this platform")
    
    def get_windows_version(self) -> Tuple[int, int, int]:
        """
        Get Windows version information
        
        Returns:
            Tuple of (major, minor, build) version numbers
        """
        if not self.is_windows:
            return (0, 0, 0)
            
        try:
            if HAS_WIN32:
                info = win32api.GetVersionEx()
                return (info[0], info[1], info[2])
            else:
                # Fallback using ctypes
                class OSVERSIONINFOEXW(ctypes.Structure):
                    _fields_ = [
                        ("dwOSVersionInfoSize", ctypes.c_ulong),
                        ("dwMajorVersion", ctypes.c_ulong),
                        ("dwMinorVersion", ctypes.c_ulong),
                        ("dwBuildNumber", ctypes.c_ulong),
                        ("dwPlatformId", ctypes.c_ulong),
                        ("szCSDVersion", ctypes.c_wchar * 128),
                        ("wServicePackMajor", ctypes.c_ushort),
                        ("wServicePackMinor", ctypes.c_ushort),
                        ("wSuiteMask", ctypes.c_ushort),
                        ("wProductType", ctypes.c_byte),
                        ("wReserved", ctypes.c_byte)
                    ]
                
                os_version = OSVERSIONINFOEXW()
                os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
                retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
                
                if retcode == 0:  # STATUS_SUCCESS
                    return (os_version.dwMajorVersion, os_version.dwMinorVersion, os_version.dwBuildNumber)
                else:
                    return (0, 0, 0)
        except Exception as e:
            logger.error(f"Error getting Windows version: {str(e)}")
            return (0, 0, 0)
    
    def add_context_menu_for_all_files(self) -> bool:
        """
        Add context menu entries for all files
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Create registry entries for all files
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\DeepSeek") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open with DeepSeek-Coder")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{self.app_path},0")
            
            # Create command key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\DeepSeek\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.app_path}" "%1"')
            
            logger.info("Added DeepSeek-Coder to context menu for all files")
            return True
            
        except Exception as e:
            logger.error(f"Error adding context menu for all files: {str(e)}")
            return False
    
    def add_context_menu_for_directory(self) -> bool:
        """
        Add context menu entries for directories
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Create registry entries for directory background
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\DeepSeekDir") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open in DeepSeek-Coder")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{self.app_path},0")
            
            # Create command key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\DeepSeekDir\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.app_path}" "%V"')
            
            # Create registry entries for directory itself
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\DeepSeekDir") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open in DeepSeek-Coder")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{self.app_path},0")
            
            # Create command key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\DeepSeekDir\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.app_path}" "%1"')
            
            logger.info("Added DeepSeek-Coder to context menu for directories")
            return True
            
        except Exception as e:
            logger.error(f"Error adding context menu for directories: {str(e)}")
            return False
    
    def add_submenu_actions(self) -> bool:
        """
        Add submenu actions to the DeepSeek-Coder context menu
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Add actions to file context menu
            actions = [
                ("Analyze with DeepSeek", f'"{self.app_path}" --analyze "%1"'),
                ("Enhance Code", f'"{self.app_path}" --enhance "%1"'),
                ("Acquire Knowledge", f'"{self.app_path}" --learn "%1"')
            ]
            
            for idx, (name, command) in enumerate(actions):
                action_key = f"*\\shell\\DeepSeek_{idx}"
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, action_key) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, name)
                    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{self.app_path},0")
                
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{action_key}\\command") as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
            
            logger.info("Added submenu actions to context menu")
            return True
            
        except Exception as e:
            logger.error(f"Error adding submenu actions: {str(e)}")
            return False
    
    def remove_context_menu_items(self) -> bool:
        """
        Remove all DeepSeek-Coder context menu items
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        keys_to_delete = [
            r"*\shell\DeepSeek",
            r"Directory\Background\shell\DeepSeekDir",
            r"Directory\shell\DeepSeekDir"
        ]
        
        # Add action keys
        for i in range(5):  # Assuming we never add more than 5 actions
            keys_to_delete.append(f"*\\shell\\DeepSeek_{i}")
        
        success = True
        for key_path in keys_to_delete:
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            except FileNotFoundError:
                # Key doesn't exist, which is fine
                pass
            except Exception as e:
                logger.error(f"Error removing registry key {key_path}: {str(e)}")
                success = False
        
        if success:
            logger.info("Removed DeepSeek-Coder context menu items")
            
        return success
    
    def register_file_associations(self, extensions: List[str]) -> bool:
        """
        Register file associations for specified extensions
        
        Args:
            extensions: List of file extensions (e.g., ['.py', '.js'])
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Register application in RegisteredApplications
            progid = "DeepSeek.CodeFile"
            
            # Create ProgID
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{progid}") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "DeepSeek-Coder Code File")
                
            # Set icon
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{progid}\DefaultIcon") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{self.app_path},0")
                
            # Set open command
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{progid}\shell\open\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.app_path}" "%1"')
            
            # Register extensions
            for ext in extensions:
                # Normalize extension
                if not ext.startswith('.'):
                    ext = f".{ext}"
                    
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{ext}") as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, progid)
            
            # Notify Windows about the changes
            if HAS_WIN32:
                win32gui.SendMessage(
                    win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, "AssociationChanged")
            
            logger.info(f"Registered file associations for {len(extensions)} extensions")
            return True
            
        except Exception as e:
            logger.error(f"Error registering file associations: {str(e)}")
            return False
    
    def create_start_menu_shortcut(self) -> bool:
        """
        Create start menu shortcut
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows or not HAS_WIN32:
            return False
        
        try:
            # Get start menu programs folder
            shell_obj = win32com.client.Dispatch("WScript.Shell")
            startmenu_dir = shell_obj.SpecialFolders("Programs")
            shortcut_path = os.path.join(startmenu_dir, "DeepSeek-Coder.lnk")
            
            # Create shortcut
            shortcut = shell_obj.CreateShortCut(shortcut_path)
            shortcut.TargetPath = self.app_path
            shortcut.WorkingDirectory = self.app_dir
            shortcut.Description = "DeepSeek-Coder - AI-powered code intelligence"
            shortcut.IconLocation = f"{self.app_path},0"
            shortcut.save()
            
            logger.info(f"Created start menu shortcut: {shortcut_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating start menu shortcut: {str(e)}")
            return False
    
    def register_protocol_handler(self, protocol: str = "deepseek") -> bool:
        """
        Register a custom URL protocol handler
        
        Args:
            protocol: Protocol name (default: deepseek)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Register protocol handler
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Set icon
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}\DefaultIcon") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{self.app_path},0")
            
            # Set open command
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}\shell\open\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.app_path}" --url "%1"')
            
            logger.info(f"Registered URL protocol handler: {protocol}://")
            return True
            
        except Exception as e:
            logger.error(f"Error registering protocol handler: {str(e)}")
            return False
    
    def setup_auto_start(self) -> bool:
        """
        Configure application to start automatically with Windows
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Add to Run registry key
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                winreg.SetValueEx(key, "DeepSeek-Coder", 0, winreg.REG_SZ, f'"{self.app_path}" --background')
            
            logger.info("Configured DeepSeek-Coder to start with Windows")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up auto start: {str(e)}")
            return False
    
    def remove_auto_start(self) -> bool:
        """
        Remove application from Windows auto start
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            # Remove from Run registry key
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                try:
                    winreg.DeleteValue(key, "DeepSeek-Coder")
                except FileNotFoundError:
                    # Key doesn't exist, which is fine
                    pass
            
            logger.info("Removed DeepSeek-Coder from Windows auto start")
            return True
            
        except Exception as e:
            logger.error(f"Error removing auto start: {str(e)}")
            return False
    
    def send_notification(self, title: str, message: str, icon_type: str = "info") -> bool:
        """
        Send a system notification
        
        Args:
            title: Notification title
            message: Notification message
            icon_type: Icon type (info, warning, error)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_windows:
            return False
        
        try:
            if HAS_WIN32:
                # Set icon flags
                flags = {
                    "info": 0x10,      # NIIF_INFO
                    "warning": 0x02,   # NIIF_WARNING
                    "error": 0x03      # NIIF_ERROR
                }.get(icon_type.lower(), 0x10)  # Default to info
                
                # Create notification
                from win32api import GetModuleHandle
                from win32gui import LoadIcon, LoadImage, NIM_ADD, NIM_DELETE, NIM_MODIFY
                from win32gui import NIIF_INFO, NIF_INFO, NIF_ICON, NIF_MESSAGE, NIF_TIP
                from win32gui import Shell_NotifyIcon
                
                # Create window for notification
                wc = win32gui.WNDCLASS()
                wc.hInstance = GetModuleHandle(None)
                wc.lpszClassName = "DeepSeekNotification"
                wc.lpfnWndProc = {win32con.WM_DESTROY: lambda hwnd, msg, wparam, lparam: win32gui.PostQuitMessage(0)}
                
                # Register window class and create window
                class_atom = win32gui.RegisterClass(wc)
                hwnd = win32gui.CreateWindow(class_atom, "DeepSeek Notification", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)
                
                # Load icon
                icon_path = self.app_path
                icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
                
                # Create notification data
                nid = (hwnd, 0, NIF_ICON | NIF_MESSAGE | NIF_TIP | NIF_INFO, win32con.WM_USER + 20,
                       icon, "DeepSeek", message, 200, title, flags)
                
                # Show notification
                Shell_NotifyIcon(NIM_ADD, nid)
                
                # Wait briefly then remove notification
                time.sleep(5)
                Shell_NotifyIcon(NIM_DELETE, (hwnd, 0))
                win32gui.DestroyWindow(hwnd)
                win32gui.UnregisterClass(class_atom, wc.hInstance)
                
                return True
            else:
                # Fallback to printing message if win32api not available
                print(f"{title}: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def get_temp_dir(self) -> str:
        """
        Get appropriate temporary directory
        
        Returns:
            Path to temporary directory
        """
        try:
            # Try to create a directory within the system temp directory
            app_temp_dir = os.path.join(tempfile.gettempdir(), "DeepSeek-Coder")
            os.makedirs(app_temp_dir, exist_ok=True)
            return app_temp_dir
        except Exception as e:
            logger.warning(f"Could not create temp directory: {str(e)}")
            # Fallback to system temp directory
            return tempfile.gettempdir()
    
    def get_app_data_dir(self) -> str:
        """
        Get appropriate location for application data
        
        Returns:
            Path to application data directory
        """
        if self.is_windows:
            # Use %APPDATA% on Windows
            app_data = os.environ.get("APPDATA")
            if app_data:
                app_dir = os.path.join(app_data, "DeepSeek-Coder")
                os.makedirs(app_dir, exist_ok=True)
                return app_dir
        
        # Fallback to ~/.deepseek-coder
        home_dir = os.path.expanduser("~")
        app_dir = os.path.join(home_dir, ".deepseek-coder")
        os.makedirs(app_dir, exist_ok=True)
        return app_dir

def get_windows_integration() -> Optional[WindowsIntegration]:
    """
    Get WindowsIntegration instance if running on Windows
    
    Returns:
        WindowsIntegration instance or None if not on Windows
    """
    if sys.platform.startswith('win'):
        # Try to find the main executable path
        if hasattr(sys, 'frozen'):  # Running as an executable
            app_path = sys.executable
        else:  # Running as a script
            try:
                import __main__
                app_path = os.path.abspath(__main__.__file__)
            except (ImportError, AttributeError):
                app_path = os.path.abspath(sys.argv[0])
        
        return WindowsIntegration(app_path)
    else:
        return None

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Get WindowsIntegration instance
    integration = get_windows_integration()
    
    if integration:
        print("Windows Integration Demo")
        print(f"App path: {integration.app_path}")
        
        # Get Windows version
        ver = integration.get_windows_version()
        print(f"Windows version: {ver[0]}.{ver[1]}.{ver[2]}")
        
        # Show notification
        integration.send_notification("DeepSeek-Coder Demo", "Windows integration is working!", "info")
        
        # Print data directories
        print(f"App data directory: {integration.get_app_data_dir()}")
        print(f"Temp directory: {integration.get_temp_dir()}")
    else:
        print("Windows integration not available on this platform")
