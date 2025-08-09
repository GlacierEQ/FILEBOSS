""
GUI Resources

This module provides resources like icons and styles for the FileBoss GUI.
"""

from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize
import os

class Icons:
    """Class containing all icons used in the application."""
    
    # Default icon sizes
    SMALL = QSize(16, 16)
    MEDIUM = QSize(32, 32)
    LARGE = QSize(64, 64)
    
    # Theme-agnostic icons (using system theme)
    FOLDER = "folder"
    FILE = "document"
    
    # File type categories
    ARCHIVE = "application-zip"
    AUDIO = "audio-x-generic"
    CODE = "text-x-generic"
    DOCUMENT = "x-office-document"
    PDF = "application-pdf"
    PRESENTATION = "x-office-presentation"
    SPREADSHEET = "x-office-spreadsheet"
    IMAGE = "image-x-generic"
    VIDEO = "video-x-generic"
    
    # Application icons
    APP_ICON = "system-file-manager"
    ADD = "list-add"
    REMOVE = "list-remove"
    REFRESH = "view-refresh"
    SEARCH = "system-search"
    SETTINGS = "preferences-system"
    
    # Status icons
    SUCCESS = "dialog-ok"
    WARNING = "dialog-warning"
    ERROR = "dialog-error"
    INFO = "dialog-information"
    
    @classmethod
    def get_icon(cls, name: str, size: QSize = None) -> QIcon:
        """Get an icon by name with optional size."""
        # First try to get from theme
        icon = QIcon.fromTheme(name)
        
        # If not found in theme, try built-in fallback
        if icon.isNull():
            # In a real app, you'd have fallback icons in a resources directory
            # For now, we'll use the theme's generic icons
            if name == cls.FOLDER:
                return QIcon.fromTheme("folder")
            elif name == cls.FILE:
                return QIcon.fromTheme("text-x-generic")
            elif name in [cls.PDF, cls.DOCUMENT, cls.SPREADSHEET, cls.PRESENTATION]:
                return QIcon.fromTheme("x-office-document")
            elif name == cls.IMAGE:
                return QIcon.fromTheme("image-x-generic")
            elif name == cls.VIDEO:
                return QIcon.fromTheme("video-x-generic")
            elif name == cls.AUDIO:
                return QIcon.fromTheme("audio-x-generic")
            elif name == cls.ARCHIVE:
                return QIcon.fromTheme("application-zip")
            elif name == cls.CODE:
                return QIcon.fromTheme("text-x-generic")
            
            # Default fallback
            return QIcon.fromTheme("text-x-generic")
        
        # Resize icon if size is specified
        if size is not None:
            return icon.pixmap(size).toImage()
        return icon
    
    @classmethod
    def get_file_icon(cls, file_path: str) -> QIcon:
        """Get appropriate icon for a file based on its extension."""
        if os.path.isdir(file_path):
            return cls.get_icon(cls.FOLDER)
            
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Map extensions to icon names
        icon_map = {
            # Documents
            '.pdf': cls.PDF,
            '.doc': cls.DOCUMENT, '.docx': cls.DOCUMENT, '.odt': cls.DOCUMENT, '.rtf': cls.DOCUMENT, '.txt': cls.DOCUMENT,
            '.xls': cls.SPREADSHEET, '.xlsx': cls.SPREADSHEET, '.ods': cls.SPREADSHEET, '.csv': cls.SPREADSHEET,
            '.ppt': cls.PRESENTATION, '.pptx': cls.PRESENTATION, '.odp': cls.PRESENTATION,
            
            # Images
            '.jpg': cls.IMAGE, '.jpeg': cls.IMAGE, '.png': cls.IMAGE, '.gif': cls.IMAGE,
            '.bmp': cls.IMAGE, '.tiff': cls.IMAGE, '.svg': cls.IMAGE, '.webp': cls.IMAGE,
            
            # Audio
            '.mp3': cls.AUDIO, '.wav': cls.AUDIO, '.ogg': cls.AUDIO, '.flac': cls.AUDIO,
            
            # Video
            '.mp4': cls.VIDEO, '.avi': cls.VIDEO, '.mov': cls.VIDEO, '.wmv': cls.VIDEO,
            
            # Archives
            '.zip': cls.ARCHIVE, '.rar': cls.ARCHIVE, '.7z': cls.ARCHIVE, '.tar': cls.ARCHIVE,
            '.gz': cls.ARCHIVE, '.bz2': cls.ARCHIVE, '.xz': cls.ARCHIVE,
            
            # Code
            '.py': cls.CODE, '.js': cls.CODE, '.html': cls.CODE, '.css': cls.CODE,
            '.cpp': cls.CODE, '.h': cls.CODE, '.java': cls.CODE, '.c': cls.CODE,
            '.sh': cls.CODE, '.bat': cls.CODE, '.ps1': cls.CODE, '.json': cls.CODE,
            '.xml': cls.CODE, '.yaml': cls.CODE, '.yml': cls.CODE, '.md': cls.CODE,
        }
        
        icon_name = icon_map.get(ext, cls.FILE)
        return cls.get_icon(icon_name)


class Styles:
    """Class containing style sheets for the application."""
    
    @staticmethod
    def get_main_style() -> str:
        """Get the main application style sheet."""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QTreeView, QListView, QTableView {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px;
            }
            
            QTreeView::item:selected, QListView::item:selected, QTableView::item:selected {
                background-color: #e0e0e0;
                color: #000000;
            }
            
            QTreeView::item:hover, QListView::item:hover, QTableView::item:hover {
                background-color: #f0f0f0;
            }
            
            QDockWidget {
                border: 1px solid #d0d0d0;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(undock.png);
            }
            
            QDockWidget::title {
                text-align: left;
                padding: 4px;
                background: #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
                background: white;
            }
            
            QStatusBar {
                background: #e0e0e0;
                border-top: 1px solid #d0d0d0;
            }
            
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin: 0px;
                padding: 0px;
            }
            
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 4px 8px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """


class Colors:
    """Class containing color constants."""
    
    # Basic colors
    WHITE = "#ffffff"
    BLACK = "#000000"
    
    # Grayscale
    GRAY_LIGHT = "#f0f0f0"
    GRAY_MEDIUM = "#d0d0d0"
    GRAY_DARK = "#808080"
    
    # Accent colors
    PRIMARY = "#1976d2"
    SECONDARY = "#f57c00"
    SUCCESS = "#388e3c"
    WARNING = "#fbc02d"
    ERROR = "#d32f2f"
    INFO = "#0288d1"
    
    # Text colors
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "757575"
    TEXT_HINT = "bdbdbd"
    
    # Background colors
    BACKGROUND = "#f5f5f5"
    SURFACE = "#ffffff"
    
    @classmethod
    def get_rgba(cls, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
