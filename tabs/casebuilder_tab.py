"""
Case Builder Tab - Integrated FileBoss Case Management
Combines the existing casebuilder GUI with enhanced functionality
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton,
    QTreeView, QListView, QTextEdit, QLineEdit, QComboBox, QFormLayout,
    QProgressDialog, QMessageBox, QFileDialog, QInputDialog, QGroupBox,
    QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QStandardItemModel, QStandardItem, QThread
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon

# Import existing casebuilder components
sys.path.append(str(Path(__file__).parent.parent / "casebuilder"))
try:
    from casebuilder.services.database import DatabaseService, get_db
    from casebuilder.services.file_organizer import FileOrganizer
    from casebuilder.services.watch_service import WatchService
    from casebuilder.models import FileCategory, Case, File, Subcase
    from casebuilder.schemas import CaseCreate, FileCategory as FileCategoryEnum
    CASEBUILDER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: CaseBuilder components not available: {e}")
    CASEBUILDER_AVAILABLE = False

class CaseBuilderTab(QWidget):
    """Main case management tab integrating existing FileBoss functionality."""

    # Signals for cross-tab communication
    case_selected = pyqtSignal(str)  # case_id
    files_updated = pyqtSignal(list)  # file_list

    def __init__(self):
        super().__init__()

        # Initialize services if available
        if CASEBUILDER_AVAILABLE:
            try:
                self.db_service = DatabaseService(next(get_db()))
                self.organizer = FileOrganizer()
                self.watch_service = WatchService(self.db_service, self.organizer)
            except Exception as e:
                print(f"Error initializing CaseBuilder services: {e}")
                self.db_service = None
                self.organizer = None
                self.watch_service = None
        else:
            self.db_service = None
            self.organizer = None
            self.watch_service = None

        # UI State
        self.current_case: Optional[Case] = None
        self.current_file: Optional[File] = None

        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        """Setup the tab's user interface."""
        layout = QVBoxLayout(self)

        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        # Title and quick actions
        title_label = QLabel("📁 Case Builder - File Management & Organization")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Quick action buttons
        new_case_btn = QPushButton("New Case")
        new_case_btn.clicked.connect(self.new_case)
        header_layout.addWidget(new_case_btn)

        import_files_btn = QPushButton("Import Files")
        import_files_btn.clicked.connect(self.import_files)
        header_layout.addWidget(import_files_btn)

        watch_folder_btn = QPushButton("Watch Folder")
        watch_folder_btn.clicked.connect(self.setup_watch_folder)
        header_layout.addWidget(watch_folder_btn)

        layout.addWidget(header_frame)

        # Main content area
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Case tree and properties
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Case explorer
        case_group = QGroupBox("Case Explorer")
        case_layout = QVBoxLayout(case_group)

        self.case_tree = QTreeView()
        self.case_tree.setHeaderHidden(True)
        self.case_tree.setModel(QStandardItemModel())
        self.case_tree.selectionModel().selectionChanged.connect(self.on_case_selected)
        case_layout.addWidget(self.case_tree)

        left_layout.addWidget(case_group)

        # Properties panel
        props_group = QGroupBox("Case Properties")
        props_layout = QFormLayout(props_group)

        self.case_name_edit = QLineEdit()
        self.case_description_edit = QTextEdit()
        self.case_description_edit.setMaximumHeight(100)
        self.case_status_combo = QComboBox()
        self.case_status_combo.addItems(["Open", "In Progress", "Closed", "Archived"])

        props_layout.addRow("Name:", self.case_name_edit)
        props_layout.addRow("Status:", self.case_status_combo)
        props_layout.addRow("Description:", self.case_description_edit)

        save_props_btn = QPushButton("Save Properties")
        save_props_btn.clicked.connect(self.save_case_properties)
        props_layout.addRow(save_props_btn)

        left_layout.addWidget(props_group)
        left_panel.setMaximumWidth(350)

        # Center panel - File listing
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # File list controls
        file_controls = QHBoxLayout()
        file_label = QLabel("Case Files:")
        file_label.setStyleSheet("font-weight: bold;")
        file_controls.addWidget(file_label)

        file_controls.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_files)
        file_controls.addWidget(refresh_btn)

        center_layout.addLayout(file_controls)

        # File list view
        self.file_list = QListView()
        self.file_list.setModel(QStandardItemModel())
        self.file_list.setViewMode(QListView.ViewMode.IconMode)
        self.file_list.setIconSize(QIcon().actualSize(QIcon().availableSizes()[0] if QIcon().availableSizes() else (64, 64)))
        self.file_list.setGridSize(QIcon().actualSize(QIcon().availableSizes()[0] if QIcon().availableSizes() else (100, 100)))
        self.file_list.setSpacing(10)
        self.file_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.file_list.selectionModel().selectionChanged.connect(self.on_file_selected)

        center_layout.addWidget(self.file_list)

        # Right panel - File preview and metadata
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Preview section
        preview_group = QGroupBox("File Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("Select a file to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("border: 1px solid #555; background-color: #2a2a2a;")
        preview_layout.addWidget(self.preview_label)

        right_layout.addWidget(preview_group)

        # Metadata section
        metadata_group = QGroupBox("File Metadata")
        metadata_layout = QVBoxLayout(metadata_group)

        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMaximumHeight(150)
        metadata_layout.addWidget(self.metadata_text)

        right_layout.addWidget(metadata_group)

        # File actions
        actions_group = QGroupBox("File Actions")
        actions_layout = QVBoxLayout(actions_group)

        export_btn = QPushButton("Export File")
        export_btn.clicked.connect(self.export_selected_file)
        actions_layout.addWidget(export_btn)

        analyze_btn = QPushButton("AI Analyze")
        analyze_btn.clicked.connect(self.analyze_selected_file)
        actions_layout.addWidget(analyze_btn)

        transcribe_btn = QPushButton("Transcribe Audio")
        transcribe_btn.clicked.connect(self.transcribe_selected_file)
        actions_layout.addWidget(transcribe_btn)

        right_layout.addWidget(actions_group)
        right_panel.setMaximumWidth(300)

        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 800, 300])

        layout.addWidget(main_splitter)

        # Status bar for this tab
        status_layout = QHBoxLayout()
        self.tab_status = QLabel("Ready")
        self.tab_progress = QPushButton("●")
        self.tab_progress.setStyleSheet("QPushButton { background-color: green; border-radius: 5px; max-width: 10px; max-height: 10px; }")

        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.tab_status)
        status_layout.addStretch()
        status_layout.addWidget(self.tab_progress)

        layout.addLayout(status_layout)

    def _load_initial_data(self):
        """Load initial case data."""
        if self.db_service:
            self._load_cases()

    def _load_cases(self):
        """Load cases into the case tree."""
        if not self.db_service:
            return

        model = self.case_tree.model()
        model.clear()

        try:
            cases = self.db_service.get_cases()

            for case in cases:
                case_item = QStandardItem(case.title)
                case_item.setData(case.id, Qt.ItemDataRole.UserRole)

                # Add subcases
                for subcase in getattr(case, 'subcases', []):
                    subcase_item = QStandardItem(subcase.title)
                    subcase_item.setData(f"subcase_{subcase.id}", Qt.ItemDataRole.UserRole)
                    case_item.appendRow(subcase_item)

                model.appendRow(case_item)

        except Exception as e:
            print(f"Error loading cases: {e}")
            self.tab_status.setText(f"Error: {str(e)}")

    # Event handlers
    def on_case_selected(self, selected, deselected):
        """Handle case selection."""
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
            subcase_id = item_data[8:]
            self.load_subcase(subcase_id)
        else:
            self.load_case(item_data)
            self.case_selected.emit(str(item_data))

    def on_file_selected(self, selected, deselected):
        """Handle file selection."""
        indexes = selected.indexes()
        if not indexes:
            return

        item = self.file_list.model().itemFromIndex(indexes[0])
        if item:
            file_id = item.data(Qt.ItemDataRole.UserRole)
            self.load_file_details(file_id)

    def load_case(self, case_id: str):
        """Load case data."""
        if not self.db_service:
            return

        try:
            self.current_case = self.db_service.get_case(case_id)
            if not self.current_case:
                return

            # Update UI
            self.case_name_edit.setText(self.current_case.title)
            self.case_description_edit.setPlainText(getattr(self.current_case, 'description', '') or "")

            # Find status in combo
            status = getattr(self.current_case, 'status', 'open').capitalize()
            index = self.case_status_combo.findText(status)
            if index >= 0:
                self.case_status_combo.setCurrentIndex(index)

            # Load files
            self.load_case_files()
            self.tab_status.setText(f"Loaded case: {self.current_case.title}")

        except Exception as e:
            print(f"Error loading case: {e}")
            self.tab_status.setText(f"Error loading case: {str(e)}")

    def load_subcase(self, subcase_id: str):
        """Load subcase data."""
        # Implementation depends on subcase model structure
        pass

    def load_case_files(self, subcase_id: str = None):
        """Load files for the current case."""
        if not self.db_service or not self.current_case:
            return

        try:
            model = self.file_list.model()
            model.clear()

            # Get files - this depends on your database schema
            files = self.db_service.get_files(
                case_id=self.current_case.id,
                subcase_id=subcase_id
            ) if hasattr(self.db_service, 'get_files') else []

            for file in files:
                item = QStandardItem()
                item.setText(getattr(file, 'original_name', 'Unknown'))
                item.setData(getattr(file, 'id', None), Qt.ItemDataRole.UserRole)
                model.appendRow(item)

            self.files_updated.emit([getattr(f, 'id', None) for f in files])

        except Exception as e:
            print(f"Error loading files: {e}")

    def load_file_details(self, file_id):
        """Load details for selected file."""
        self.preview_label.setText(f"File ID: {file_id}")
        self.metadata_text.setPlainText(f"File metadata for ID: {file_id}")

    # Action handlers
    def new_case(self):
        """Create a new case."""
        name, ok = QInputDialog.getText(self, "New Case", "Enter case name:")

        if ok and name and self.db_service:
            try:
                case = CaseCreate(title=name, description="", status="open")
                db_case = self.db_service.create_case(case)
                self._load_cases()
                self.tab_status.setText(f"Created case: {name}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create case: {str(e)}")

    def import_files(self):
        """Import files into current case."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case", "Please select a case first.")
            return

        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Import")
        if files:
            self.process_files(files)

    def setup_watch_folder(self):
        """Setup folder watching."""
        if not self.current_case:
            QMessageBox.warning(self, "No Case", "Please select a case first.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Watch")
        if folder and self.watch_service:
            try:
                self.watch_service.add_watch(
                    directory=folder,
                    case_id=self.current_case.id,
                    category=FileCategory.EVIDENCE if CASEBUILDER_AVAILABLE else "evidence",
                    recursive=True
                )
                QMessageBox.information(self, "Watch Setup", f"Now watching: {folder}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to setup watch: {str(e)}")

    def process_files(self, file_paths: List[str]):
        """Process and import files."""
        if not file_paths or not self.organizer:
            return

        progress = QProgressDialog("Processing files...", "Cancel", 0, len(file_paths), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        for i, file_path in enumerate(file_paths):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            progress.setLabelText(f"Processing {os.path.basename(file_path)}...")

            try:
                self.organizer.organize_file(
                    file_path=file_path,
                    case_id=self.current_case.id
                )
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        progress.setValue(len(file_paths))
        self.load_case_files()

    def save_case_properties(self):
        """Save case property changes."""
        if not self.current_case or not self.db_service:
            return

        try:
            # Update case properties
            self.current_case.title = self.case_name_edit.text()
            if hasattr(self.current_case, 'description'):
                self.current_case.description = self.case_description_edit.toPlainText()
            if hasattr(self.current_case, 'status'):
                self.current_case.status = self.case_status_combo.currentText().lower()

            # Save to database
            self.db_service.update_case(self.current_case.id, self.current_case)
            self._load_cases()
            self.tab_status.setText("Properties saved")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")

    def refresh_files(self):
        """Refresh the file list."""
        if self.current_case:
            self.load_case_files()
            self.tab_status.setText("Files refreshed")

    def export_selected_file(self):
        """Export the selected file."""
        # Implementation for file export
        QMessageBox.information(self, "Export", "File export not yet implemented")

    def analyze_selected_file(self):
        """Send selected file for AI analysis."""
        # Signal to AI analysis tab
        QMessageBox.information(self, "AI Analysis", "Sending to AI Analysis tab...")

    def transcribe_selected_file(self):
        """Send selected file for transcription."""
        # Signal to WhisperX tab
        QMessageBox.information(self, "Transcription", "Sending to WhisperX tab...")

    # Tab interface methods
    def initialize(self):
        """Initialize the tab when the application starts."""
        if CASEBUILDER_AVAILABLE:
            self.tab_status.setText("CaseBuilder initialized")
        else:
            self.tab_status.setText("CaseBuilder unavailable - demo mode")

    def on_activated(self):
        """Called when this tab becomes active."""
        self.refresh_files()

    def cleanup(self):
        """Cleanup when application closes."""
        if self.watch_service:
            self.watch_service.stop()
