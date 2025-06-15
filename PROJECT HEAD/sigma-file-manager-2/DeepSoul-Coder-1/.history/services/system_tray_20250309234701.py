"""
System Tray - System tray integration for DeepSeek-Coder background service
"""
import os
import sys
import logging
import threading
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import PyQt for system tray
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QDialog, QVBoxLayout,
    QLabel, QListWidget, QPushButton, QWidget, QHBoxLayout,
    QCheckBox, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject

# Import background service if available
try:
    from services.background_service import BackgroundService
except ImportError:
    BackgroundService = None

logger = logging.getLogger("DeepSoul-SystemTray")

class DirectoryManagerDialog(QDialog):
    """Dialog for managing watched directories"""
    
    directories_changed = pyqtSignal(list)
    
    def __init__(self, directories=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Watched Directories")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # Initialize directories
        self.directories = directories or []
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add description
        layout.addWidget(QLabel("Directories being monitored for file changes:"))
        
        # Create directory list
        self.dir_list = QListWidget()
        for directory in self.directories:
            self.dir_list.addItem(directory)
        layout.addWidget(self.dir_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Directory")
        self.add_button.clicked.connect(self.add_directory)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_directory)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)
        
        # Add close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
    
    def add_directory(self):
        """Add a directory to the watch list"""
        # Import here to avoid circular imports
        from PyQt6.QtWidgets import QFileDialog
        
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Watch")
        if directory:
            # Check if already in list
            for i in range(self.dir_list.count()):
                if self.dir_list.item(i).text() == directory:
                    return
            
            # Add to list
            self.dir_list.addItem(directory)
            self.directories.append(directory)
            self.directories_changed.emit(self.directories)
    
    def remove_directory(self):
        """Remove selected directory from watch list"""
        selected_items = self.dir_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            # Remove from list widget
            row = self.dir_list.row(item)
            self.dir_list.takeItem(row)
            
            # Remove from directory list
            directory = item.text()
            if directory in self.directories:
                self.directories.remove(directory)
        
        self.directories_changed.emit(self.directories)

class TaskManagerDialog(QDialog):
    """Dialog for managing tasks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DeepSeek Task Manager")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add description
        layout.addWidget(QLabel("Current and recent DeepSeek tasks:"))
        
        # Create task list
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_tasks)
        
        self.cancel_button = QPushButton("Cancel Selected")
        self.cancel_button.clicked.connect(self.cancel_task)
        
        self.clear_button = QPushButton("Clear Completed")
        self.clear_button.clicked.connect(self.clear_completed)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        # Add close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        
        # Populate tasks (dummy data for now)
        self.refresh_tasks()
    
    def refresh_tasks(self):
        """Refresh task list"""
        self.task_list.clear()
        
        # In a real implementation, these would come from the background service
        # For now, just add some sample tasks
        self.task_list.addItem("File Analysis: main.py (Completed)")
        self.task_list.addItem("File Monitoring: /home/user/projects (Running)")
        self.task_list.addItem("Code Enhancement: utils.py (Pending)")
    
    def cancel_task(self):
        """Cancel selected task"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
            
        # In a real implementation, this would send a cancel message to the background service
        QMessageBox.information(self, "Cancel Task", "Task cancellation not implemented yet")
    
    def clear_completed(self):
        """Clear completed tasks"""
        # In a real implementation, this would clear completed tasks from the service
        for i in range(self.task_list.count() - 1, -1, -1):
            item = self.task_list.item(i)
            if "(Completed)" in item.text() or "(Failed)" in item.text():
                self.task_list.takeItem(i)

class SettingsDialog(QDialog):
    """Dialog for configuring settings"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DeepSeek Settings")
        self.setMinimumWidth(500)
        
        # Initialize settings
        self.settings = settings or {}
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Auto features
        auto_group_box = QWidget()
        auto_layout = QVBoxLayout(auto_group_box)
        
        self.auto_analyze_check = QCheckBox("Automatically analyze modified code files")
        self.auto_analyze_check.setChecked(self.settings.get("auto_analyze", False))
        
        self.auto_enhance_check = QCheckBox("Automatically enhance code on demand")
        self.auto_enhance_check.setChecked(self.settings.get("auto_enhance", False))
        
        self.auto_learn_check = QCheckBox("Automatically learn from new code files")
        self.auto_learn_check.setChecked(self.settings.get("auto_learn", False))
        
        auto_layout.addWidget(self.auto_analyze_check)
        auto_layout.addWidget(self.auto_enhance_check)
        auto_layout.addWidget(self.auto_learn_check)
        
        layout.addWidget(auto_group_box)
        
        # Startup options
        startup_box = QWidget()
        startup_layout = QVBoxLayout(startup_box)
        
        self.startup_check = QCheckBox("Start DeepSeek-Coder with Windows")
        self.startup_check.setChecked(self.settings.get("auto_start", False))
        
        startup_layout.addWidget(self.startup_check)
        layout.addWidget(startup_box)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def save_settings(self):
        """Save settings and close dialog"""
        # Update settings dictionary
        self.settings.update({
            "auto_analyze": self.auto_analyze_check.isChecked(),
            "auto_enhance": self.auto_enhance_check.isChecked(),
            "auto_learn": self.auto_learn_check.isChecked(),
            "auto_start": self.startup_check.isChecked()
        })
        
        # Emit signal with updated settings
        self.settings_changed.emit(self.settings)
        
        # Close dialog
        self.accept()

class AboutDialog(QDialog):
    """About dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About DeepSeek-Coder")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add logo (placeholder)
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # In a real implementation, this would display a logo
        layout.addWidget(logo_label)
        
        # Add app name and version
        app_label = QLabel("DeepSeek-Coder")
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(app_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Add description
        desc_label = QLabel(
            "DeepSeek-Coder is an AI-powered code intelligence system that "
            "provides deep understanding, enhancement, and generation capabilities for code.")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Add copyright
        copyright_label = QLabel("© 2023 DeepSeek AI")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
        
        # Add close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon for DeepSeek-Coder background service"""
    
    def __init__(self, service=None):
        """
        Initialize the system tray icon
        
        Args:
            service: Optional BackgroundService instance
        """
        # Create default icon
        icon = self._get_default_icon()
        super().__init__(icon)
        
        # Store service
        self.service = service
        
        # Set tooltip
        self.setToolTip("DeepSeek-Coder")
        
        # Create context menu
        self.menu = self._create_menu()
        self.setContextMenu(self.menu)
        
        # Connect signal
        self.activated.connect(self.on_activated)
        
        # Show notification on startup
        self.showMessage(
            "DeepSeek-Coder",
            "Background service is running",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def _create_menu(self) -> QMenu:
        """Create the tray context menu"""
        menu = QMenu()
        
        # Open main UI action
        open_ui_action = menu.addAction("Open DeepSeek-Coder")
        open_ui_action.triggered.connect(self.open_main_ui)
        
        menu.addSeparator()
        
        # Directories submenu
        directories_action = menu.addAction("Watched Directories...")
        directories_action.triggered.connect(self.show_directories_dialog)
        
        # Tasks submenu
        tasks_action = menu.addAction("Task Manager...")
        tasks_action.triggered.connect(self.show_tasks_dialog)
        
        # Settings action
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.show_settings_dialog)
        
        menu.addSeparator()
        
        # About action
        about_action = menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)
        
        # Quit action
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        return menu
    
    def _get_default_icon(self) -> QIcon:
        """Get the default tray icon"""
        # Try to load icon from resources
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            # Create a simple colored icon as fallback
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.blue)
            return QIcon(pixmap)
    
    def on_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_main_ui()
    
    def open_main_ui(self):
        """Open the main UI application"""
        try:
            # Launch main UI process
            script_path = os.path.join(os.path.dirname(__file__), "..", "gui", "desktop_app.py")
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
            else:
                # Try the executable
                app_path = os.path.join(os.path.dirname(__file__), "..", "DeepSeek-Coder.exe")
                if os.path.exists(app_path):
                    subprocess.Popen([app_path])
                else:
                    self.showMessage("Error", "Could not find application", QSystemTrayIcon.MessageIcon.Warning)
        except Exception as e:
            logger.error(f"Error launching main UI: {str(e)}")
            self.showMessage("Error", f"Could not launch application: {str(e)}", QSystemTrayIcon.MessageIcon.Critical)
    
    def show_directories_dialog(self):
        """Show dialog for managing watched directories"""
        # Get current directories from service
        current_dirs = []
        if self.service:
            current_dirs = self.service.watched_directories
        
        # Create and show dialog
        dialog = DirectoryManagerDialog(current_dirs)
        dialog.directories_changed.connect(self._update_watched_directories)
        dialog.exec()
    
    def _update_watched_directories(self, directories):
        """Handle directories being updated from dialog"""
        if self.service:
            # Update config with new directories
            self.service.submit_task("update_config", {"config": {"watched_directories": directories}}, priority=0)
    
    def show_tasks_dialog(self):
        """Show task manager dialog"""
        dialog = TaskManagerDialog()
        dialog.exec()
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        # Get current settings from service
        current_settings = {}
        if self.service:
            current_settings = self.service.config
        
        # Create and show dialog
        dialog = SettingsDialog(current_settings)
        dialog.settings_changed.connect(self._update_settings)
        dialog.exec()
    
    def _update_settings(self, settings):
        """Handle settings being updated from dialog"""
        if self.service:
            # Update config with new settings
            self.service.submit_task("update_config", {"config": settings}, priority=0)
    
    def show_about_dialog(self):
        """Show about dialog"""
        dialog = AboutDialog()
        dialog.exec()
    
    def quit_application(self):
        """Quit the application"""
        if self.service:
            # Stop the service
            self.service.stop()
        
        # Quit application
        QApplication.quit()

def run_system_tray():
    """Run the system tray application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("deepsoul_systemtray.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when all windows are closed
    
    # Get service instance if possible
    service = None
    if len(sys.argv) > 1 and sys.argv[1] == "--with-service":
        service = BackgroundService()
        service.start()
    
    # Create and show tray icon
    tray_icon = SystemTrayIcon(service)
    tray_icon.show()
    
    # Run application
    exit_code = app.exec()
    
    # Clean up
    if service:
        service.stop()
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_system_tray())
