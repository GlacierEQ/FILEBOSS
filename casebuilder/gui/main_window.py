"""
Main Window for FileBoss GUI

This module provides the main application window with a modern interface.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTreeView, QFileSystemModel, QListView,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox, QDockWidget,
    QTabWidget, QFormLayout, QLineEdit, QTextEdit, QComboBox, QToolBar,
    QApplication, QStyle, QSizePolicy, QProgressBar, QToolButton
)
from PyQt6.QtCore import Qt, QSize, QModelIndex, QSortFilterProxyModel, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem, QPixmap

from ..services.database import DatabaseService, get_db
from ..services.file_organizer import FileOrganizer
from ..services.watch_service import WatchService
from ..models import FileCategory, Case, File, Subcase
from ..schemas import CaseCreate, FileCategory as FileCategoryEnum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileBossMainWindow(QMainWindow):
    """Main application window for FileBoss."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize services
        self.db_service = DatabaseService(next(get_db()))
        self.organizer = FileOrganizer()
        self.watch_service = WatchService(self.db_service, self.organizer)
        
        # UI State
        self.current_case: Optional[Case] = None
        self.current_file: Optional[File] = None
        
        # Setup UI
        self.setWindowTitle("FileBoss - Case Management System")
        self.setMinimumSize(1024, 768)
        
        # Create UI components
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bars()
        self._create_status_bar()
        self._create_dock_widgets()
        self._create_central_widget()
        
        # Load initial data
        self._load_cases()
        
    def _create_actions(self):
        """Create actions for menus and toolbars."""
        # File actions
        self.new_case_action = QAction("&New Case", self)
        self.new_case_action.triggered.connect(self.new_case)
        self.new_case_action.setShortcut("Ctrl+N")
        
        self.open_case_action = QAction("&Open Case...", self)
        self.open_case_action.triggered.connect(self.open_case)
        self.open_case_action.setShortcut("Ctrl+O")
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.triggered.connect(self.close)
        self.exit_action.setShortcut("Alt+F4")
        
        # Edit actions
        self.add_files_action = QAction("Add &Files...", self)
        self.add_files_action.triggered.connect(self.add_files)
        self.add_files_action.setShortcut("Ctrl+F")
        
        self.add_folder_action = QAction("Add &Folder...", self)
        self.add_folder_action.triggered.connect(self.add_folder)
        self.add_folder_action.setShortcut("Ctrl+D")
        
        # View actions
        self.toggle_case_view_action = QAction("&Case Explorer", self)
        self.toggle_case_view_action.setCheckable(True)
        self.toggle_case_view_action.setChecked(True)
        self.toggle_case_view_action.triggered.connect(self.toggle_case_view)
        
        self.toggle_properties_action = QAction("&Properties", self)
        self.toggle_properties_action.setCheckable(True)
        self.toggle_properties_action.setChecked(True)
        self.toggle_properties_action.triggered.connect(self.toggle_properties)
        
        # Tools actions
        self.watch_folder_action = QAction("&Watch Folder...", self)
        self.watch_folder_action.triggered.connect(self.watch_folder)
        
        self.export_case_action = QAction("&Export Case...", self)
        self.export_case_action.triggered.connect(self.export_case)
        
        # Help actions
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.about)
        
    def _create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_case_action)
        file_menu.addAction(self.open_case_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_case_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.add_files_action)
        edit_menu.addAction(self.add_folder_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.toggle_case_view_action)
        view_menu.addAction(self.toggle_properties_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction(self.watch_folder_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self.about_action)
    
    def _create_tool_bars(self):
        """Create toolbars."""
        # Main toolbar
        main_toolbar = self.addToolBar("Main Toolbar")
        main_toolbar.setMovable(False)
        
        # Add actions to toolbar
        main_toolbar.addAction(self.new_case_action)
        main_toolbar.addAction(self.open_case_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.add_files_action)
        main_toolbar.addAction(self.add_folder_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.watch_folder_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add status widgets
        self.status_label = QLabel("Ready")
        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.setVisible(False)
        
        self.statusBar.addPermanentWidget(self.status_label, 1)
        self.statusBar.addPermanentWidget(self.status_progress)
    
    def _create_dock_widgets(self):
        """Create dockable widgets."""
        # Case Explorer Dock
        self.case_dock = QDockWidget("Case Explorer", self)
        self.case_dock.setObjectName("CaseExplorerDock")
        self.case_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                      Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Case tree view
        self.case_tree = QTreeView()
        self.case_tree.setHeaderHidden(True)
        self.case_tree.setModel(QStandardItemModel())
        self.case_tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.case_tree.selectionModel().selectionChanged.connect(self.on_case_selected)
        
        self.case_dock.setWidget(self.case_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.case_dock)
        
        # Properties Dock
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setObjectName("PropertiesDock")
        self.properties_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | 
                                           Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Properties widget
        self.properties_widget = QWidget()
        self.properties_layout = QFormLayout()
        
        # Add property fields
        self.case_name_edit = QLineEdit()
        self.case_description_edit = QTextEdit()
        self.case_status_combo = QComboBox()
        self.case_status_combo.addItems(["Open", "In Progress", "Closed", "Archived"])
        
        self.properties_layout.addRow("Name:", self.case_name_edit)
        self.properties_layout.addRow("Status:", self.case_status_combo)
        self.properties_layout.addRow("Description:", self.case_description_edit)
        
        # Add save button
        self.save_properties_btn = QPushButton("Save Changes")
        self.save_properties_btn.clicked.connect(self.save_properties)
        self.properties_layout.addRow(self.save_properties_btn)
        
        self.properties_widget.setLayout(self.properties_layout)
        self.properties_dock.setWidget(self.properties_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)
    
    def _create_central_widget(self):
        """Create the central widget."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File list view
        self.file_list = QListView()
        self.file_list.setModel(QStandardItemModel())
        self.file_list.setViewMode(QListView.ViewMode.IconMode)
        self.file_list.setIconSize(QSize(64, 64))
        self.file_list.setGridSize(QSize(100, 100))
        self.file_list.setSpacing(10)
        self.file_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.file_list.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        
        splitter.addWidget(self.file_list)
        
        # Preview panel
        self.preview_widget = QWidget()
        preview_layout = QVBoxLayout(self.preview_widget)
        
        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.metadata_text)
        
        splitter.addWidget(self.preview_widget)
        splitter.setSizes([self.width() * 0.7, self.width() * 0.3])
        
        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)
    
    # Data loading methods
    def _load_cases(self):
        """Load cases into the case tree."""
        model = self.case_tree.model()
        model.clear()
        
        # Get all cases
        try:
            cases = self.db_service.get_cases()
            
            for case in cases:
                case_item = QStandardItem(case.title)
                case_item.setData(case.id, Qt.ItemDataRole.UserRole)
                case_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                
                # Add subcases
                for subcase in case.subcases:
                    subcase_item = QStandardItem(subcase.title)
                    subcase_item.setData(f"subcase_{subcase.id}", Qt.ItemDataRole.UserRole)
                    subcase_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    case_item.appendRow(subcase_item)
                
                model.appendRow(case_item)
                
        except Exception as e:
            logger.error(f"Error loading cases: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load cases: {str(e)}")
    
    # Event handlers
    def on_case_selected(self, selected, deselected):
        """Handle case selection change."""
        indexes = selected.indexes()
        if not indexes:
            return
            
        item = self.case_tree.model().itemFromIndex(indexes[0])
        if not item:
            return
            
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        if isinstance(item_data, str) and item_data.startswith("subcase_"):
            # Handle subcase selection
            subcase_id = item_data[8:]  # Remove 'subcase_'
            self.load_subcase(subcase_id)
        else:
            # Handle case selection
            self.load_case(item_data)
    
    def load_case(self, case_id: str):
        """Load a case's data into the UI."""
        try:
            self.current_case = self.db_service.get_case(case_id)
            if not self.current_case:
                return
                
            # Update UI
            self.case_name_edit.setText(self.current_case.title)
            self.case_description_edit.setPlainText(self.current_case.description or "")
            index = self.case_status_combo.findText(self.current_case.status.capitalize())
            if index >= 0:
                self.case_status_combo.setCurrentIndex(index)
                
            # Load files
            self.load_case_files()
            
        except Exception as e:
            logger.error(f"Error loading case: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load case: {str(e)}")
    
    def load_subcase(self, subcase_id: str):
        """Load a subcase's data into the UI."""
        try:
            subcase = self.db_service.get_subcase(subcase_id)
            if not subcase:
                return
                
            # Load the parent case
            self.load_case(subcase.case_id)
            
            # Update UI for subcase
            self.case_name_edit.setText(f"{self.current_case.title} > {subcase.title}")
            
            # Load files for subcase
            self.load_case_files(subcase_id)
            
        except Exception as e:
            logger.error(f"Error loading subcase: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load subcase: {str(e)}")
    
    def load_case_files(self, subcase_id: str = None):
        """Load files for the current case/subcase."""
        try:
            if not self.current_case:
                return
                
            model = self.file_list.model()
            model.clear()
            
            # Get files for case/subcase
            files = self.db_service.get_files(
                case_id=self.current_case.id,
                subcase_id=subcase_id
            )
            
            # Add files to the list
            for file in files:
                item = QStandardItem()
                item.setText(file.original_name)
                item.setData(file.id, Qt.ItemDataRole.UserRole)
                
                # Set appropriate icon based on file type
                if file.mime_type and file.mime_type.startswith('image/'):
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                elif file.mime_type == 'application/pdf':
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                else:
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                
                model.appendRow(item)
                
        except Exception as e:
            logger.error(f"Error loading files: {e}")
    
    # Action handlers
    def new_case(self):
        """Create a new case."""
        name, ok = QInputDialog.getText(
            self, 
            "New Case", 
            "Enter case name:",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and name:
            try:
                case = CaseCreate(
                    title=name,
                    description="",
                    status="open"
                )
                
                db_case = self.db_service.create_case(case)
                self._load_cases()
                
                # Select the new case
                self.select_case_in_tree(db_case.id)
                
            except Exception as e:
                logger.error(f"Error creating case: {e}")
                QMessageBox.critical(self, "Error", f"Failed to create case: {str(e)}")
    
    def open_case(self):
        """Open an existing case."""
        # In a real app, this would show a dialog to select a case
        # For now, just reload the cases
        self._load_cases()
    
    def add_files(self):
        """Add files to the current case/subcase."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case Selected", "Please select a case first.")
            return
            
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            
            # Get the current subcase ID if in a subcase
            subcase_id = None
            current_index = self.case_tree.currentIndex()
            if current_index.isValid():
                item = self.case_tree.model().itemFromIndex(current_index)
                item_data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(item_data, str) and item_data.startswith("subcase_"):
                    subcase_id = item_data[8:]
            
            # Process files
            self.process_files(file_paths, subcase_id)
    
    def add_folder(self):
        """Add a folder of files to the current case/subcase."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case Selected", "Please select a case first.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder:
            # Get all files in the folder recursively
            file_paths = []
            for root, _, files in os.walk(folder):
                for file in files:
                    file_paths.append(os.path.join(root, file))
            
            if file_paths:
                # Get the current subcase ID if in a subcase
                subcase_id = None
                current_index = self.case_tree.currentIndex()
                if current_index.isValid():
                    item = self.case_tree.model().itemFromIndex(current_index)
                    item_data = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, str) and item_data.startswith("subcase_"):
                        subcase_id = item_data[8:]
                
                # Process files
                self.process_files(file_paths, subcase_id)
    
    def process_files(self, file_paths: List[str], subcase_id: str = None):
        """Process and add files to the current case/subcase."""
        if not file_paths:
            return
            
        try:
            # Show progress
            progress = QProgressDialog("Processing files...", "Cancel", 0, len(file_paths), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(1000)
            
            for i, file_path in enumerate(file_paths):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                progress.setLabelText(f"Processing {os.path.basename(file_path)}...")
                
                try:
                    # Process the file
                    self.organizer.organize_file(
                        file_path=file_path,
                        case_id=self.current_case.id,
                        subcase_id=subcase_id
                    )
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
            
            progress.setValue(len(file_paths))
            
            # Refresh the file list
            if subcase_id:
                self.load_subcase(subcase_id)
            else:
                self.load_case(self.current_case.id)
                
        except Exception as e:
            logger.error(f"Error in process_files: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process files: {str(e)}")
    
    def watch_folder(self):
        """Set up a watch folder for automatic processing."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case Selected", "Please select a case first.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Watch")
        
        if folder:
            try:
                # Get the current subcase ID if in a subcase
                subcase_id = None
                current_index = self.case_tree.currentIndex()
                if current_index.isValid():
                    item = self.case_tree.model().itemFromIndex(current_index)
                    item_data = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, str) and item_data.startswith("subcase_"):
                        subcase_id = item_data[8:]
                
                # Add the watch
                self.watch_service.add_watch(
                    directory=folder,
                    case_id=self.current_case.id,
                    subcase_id=subcase_id,
                    category=FileCategory.EVIDENCE,
                    recursive=True
                )
                
                QMessageBox.information(
                    self, 
                    "Watch Folder Added", 
                    f"Now watching folder: {folder}\n"
                    f"Files will be automatically added to case: {self.current_case.title}"
                )
                
            except Exception as e:
                logger.error(f"Error setting up watch folder: {e}")
                QMessageBox.critical(self, "Error", f"Failed to set up watch folder: {str(e)}")
    
    def export_case(self):
        """Export the current case to a file."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case Selected", "Please select a case first.")
            return
            
        # In a real app, this would export the case to a file
        QMessageBox.information(
            self, 
            "Export Case", 
            f"Exporting case: {self.current_case.title}\n"
            "This feature is not yet implemented."
        )
    
    def save_properties(self):
        """Save changes to the current case's properties."""
        if not self.current_case:
            return
            
        try:
            # Update case properties
            self.current_case.title = self.case_name_edit.text()
            self.current_case.description = self.case_description_edit.toPlainText()
            self.current_case.status = self.case_status_combo.currentText().lower()
            
            # Save to database
            self.db_service.update_case(self.current_case.id, self.current_case)
            
            # Refresh the case tree
            self._load_cases()
            
            # Reselect the current case
            self.select_case_in_tree(self.current_case.id)
            
            self.statusBar.showMessage("Changes saved successfully.", 3000)
            
        except Exception as e:
            logger.error(f"Error saving properties: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save properties: {str(e)}")
    
    def toggle_case_view(self, checked: bool):
        """Toggle the case explorer dock visibility."""
        self.case_dock.setVisible(checked)
    
    def toggle_properties(self, checked: bool):
        """Toggle the properties dock visibility."""
        self.properties_dock.setVisible(checked)
    
    def about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About FileBoss",
            "<h2>FileBoss Case Management System</h2>"
            "<p>Version 1.0.0</p>"
            "<p>© 2025 Your Company Name</p>"
            "<p>FileBoss is a powerful case management system for organizing "
            "and managing files and evidence.</p>"
        )
    
    # Helper methods
    def select_case_in_tree(self, case_id: str):
        """Select a case in the case tree by ID."""
        model = self.case_tree.model()
        
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == case_id:
                index = model.indexFromItem(item)
                self.case_tree.setCurrentIndex(index)
                break
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop any running watch services
        self.watch_service.stop()
        
        # Close the database connection
        if hasattr(self, 'db_service') and self.db_service:
            self.db_service.close()
        
        event.accept()


def run_gui():
    """Run the FileBoss GUI application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = FileBossMainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()
