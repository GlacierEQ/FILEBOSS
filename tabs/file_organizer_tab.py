"""
File Organizer Tab - Advanced File Organization & Management
Integrates the Local File Organizer with AI-powered organization
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QSpinBox, QProgressBar,
    QFileDialog, QMessageBox, QSplitter, QFrame, QTabWidget, QSlider,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QMimeData
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QIcon, QStandardItemModel

# Import Local File Organizer components
sys.path.append(str(Path(__file__).parent.parent / "PROJECT HEAD/Local-File-Organizer-main"))
try:
    from main import (
        initialize_models, process_files_by_type, process_files_by_date,
        process_text_files, process_image_files, process_legal_documents
    )
    from file_utils import (
        display_directory_tree, collect_file_paths, separate_files_by_type,
        read_file_data, is_legal_document
    )
    from data_processing_common import compute_operations, execute_operations
    FILE_ORGANIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: File Organizer components not available: {e}")
    FILE_ORGANIZER_AVAILABLE = False

class FileOrganizationWorker(QThread):
    """Worker thread for file organization to prevent UI blocking."""

    progress_updated = pyqtSignal(int, str)  # progress, status
    file_processed = pyqtSignal(str, str)  # source, destination
    organization_complete = pyqtSignal(dict)  # results
    error_occurred = pyqtSignal(str)

    def __init__(self, source_path: str, output_path: str, mode: str, options: dict):
        super().__init__()
        self.source_path = source_path
        self.output_path = output_path
        self.mode = mode
        self.options = options
        self.should_stop = False

    def run(self):
        """Run the file organization process."""
        try:
            self.progress_updated.emit(10, "Scanning source directory...")

            # Collect file paths
            file_paths = collect_file_paths(self.source_path) if FILE_ORGANIZER_AVAILABLE else []

            if self.should_stop:
                return

            self.progress_updated.emit(30, f"Found {len(file_paths)} files...")

            # Initialize AI models if needed
            if self.options.get('use_ai', False) and FILE_ORGANIZER_AVAILABLE:
                self.progress_updated.emit(40, "Initializing AI models...")
                initialize_models()

            if self.should_stop:
                return

            self.progress_updated.emit(50, "Computing organization operations...")

            # Choose organization method based on mode
            if self.mode == "by_type":
                operations = process_files_by_type(
                    file_paths,
                    self.output_path,
                    dry_run=True,
                    silent=True
                ) if FILE_ORGANIZER_AVAILABLE else []
            elif self.mode == "by_date":
                operations = process_files_by_date(
                    file_paths,
                    self.output_path,
                    dry_run=True,
                    silent=True
                ) if FILE_ORGANIZER_AVAILABLE else []
            elif self.mode == "legal_only":
                # Filter for legal documents only
                legal_files = [f for f in file_paths if is_legal_document(f)] if FILE_ORGANIZER_AVAILABLE else []
                results = process_legal_documents(
                    legal_files,
                    self.output_path,
                    dry_run=True
                ) if FILE_ORGANIZER_AVAILABLE else {}
                operations = []  # Legal processor returns different format
            else:
                operations = []

            if self.should_stop:
                return

            self.progress_updated.emit(70, "Executing file operations...")

            # Execute operations
            if operations and FILE_ORGANIZER_AVAILABLE:
                execute_operations(operations, dry_run=False, silent=True)

                # Report each operation
                for i, op in enumerate(operations):
                    if self.should_stop:
                        break
                    self.file_processed.emit(op['source'], op['destination'])
                    progress = 70 + (20 * i // len(operations))
                    self.progress_updated.emit(progress, f"Processing {os.path.basename(op['source'])}...")

            self.progress_updated.emit(100, "Organization complete")

            # Compile results
            results = {
                'total_files': len(file_paths),
                'processed': len(operations),
                'mode': self.mode,
                'output_path': self.output_path
            }

            self.organization_complete.emit(results)

        except Exception as e:
            self.error_occurred.emit(f"Organization error: {str(e)}")

    def stop(self):
        """Stop the organization process."""
        self.should_stop = True

class FileOrganizerTab(QWidget):
    """File organization and management tab."""

    # Signals for cross-tab communication
    files_organized = pyqtSignal(list)  # organized_files
    directory_processed = pyqtSignal(str)  # directory_path

    def __init__(self):
        super().__init__()

        # State variables
        self.source_directory = None
        self.output_directory = None
        self.organization_worker = None
        self.operation_history = []
        self.file_preview_data = {}

        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self):
        """Setup the tab's user interface."""
        layout = QVBoxLayout(self)

        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("🗂️ File Organizer - Intelligent File Management")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Quick action buttons
        select_source_btn = QPushButton("Select Source")
        select_source_btn.clicked.connect(self.select_source_directory)
        header_layout.addWidget(select_source_btn)

        select_output_btn = QPushButton("Select Output")
        select_output_btn.clicked.connect(self.select_output_directory)
        header_layout.addWidget(select_output_btn)

        quick_organize_btn = QPushButton("Quick Organize")
        quick_organize_btn.clicked.connect(self.quick_organize)
        header_layout.addWidget(quick_organize_btn)

        layout.addWidget(header_frame)

        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Directory selection and settings
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Directory selection
        dir_group = QGroupBox("Directory Selection")
        dir_layout = QFormLayout(dir_group)

        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("Select source directory...")

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("Select output directory...")

        browse_source_btn = QPushButton("Browse...")
        browse_source_btn.clicked.connect(self.select_source_directory)

        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self.select_output_directory)

        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_path_edit)
        source_layout.addWidget(browse_source_btn)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(browse_output_btn)

        dir_layout.addRow("Source:", source_layout)
        dir_layout.addRow("Output:", output_layout)

        left_layout.addWidget(dir_group)

        # Organization settings
        settings_group = QGroupBox("Organization Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Organization mode
        mode_label = QLabel("Organization Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(mode_label)

        self.mode_group = QButtonGroup()

        self.type_radio = QRadioButton("By File Type")
        self.type_radio.setChecked(True)
        self.mode_group.addButton(self.type_radio, 0)
        settings_layout.addWidget(self.type_radio)

        self.date_radio = QRadioButton("By Date")
        self.mode_group.addButton(self.date_radio, 1)
        settings_layout.addWidget(self.date_radio)

        self.legal_radio = QRadioButton("Legal Documents Only")
        self.mode_group.addButton(self.legal_radio, 2)
        settings_layout.addWidget(self.legal_radio)

        self.smart_radio = QRadioButton("AI Smart Organization")
        self.mode_group.addButton(self.smart_radio, 3)
        settings_layout.addWidget(self.smart_radio)

        # Options
        options_label = QLabel("Options:")
        options_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(options_label)

        self.preserve_structure_check = QCheckBox("Preserve directory structure")
        self.preserve_structure_check.setChecked(True)
        settings_layout.addWidget(self.preserve_structure_check)

        self.copy_files_check = QCheckBox("Copy files (instead of move)")
        self.copy_files_check.setChecked(True)
        settings_layout.addWidget(self.copy_files_check)

        self.process_subdirs_check = QCheckBox("Process subdirectories")
        self.process_subdirs_check.setChecked(True)
        settings_layout.addWidget(self.process_subdirs_check)

        self.use_ai_check = QCheckBox("Use AI for content analysis")
        self.use_ai_check.setChecked(False)
        settings_layout.addWidget(self.use_ai_check)

        left_layout.addWidget(settings_group)

        # Preview section
        preview_group = QGroupBox("File Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.file_count_label = QLabel("No directory selected")
        preview_layout.addWidget(self.file_count_label)

        self.file_types_text = QTextEdit()
        self.file_types_text.setReadOnly(True)
        self.file_types_text.setMaximumHeight(120)
        self.file_types_text.setPlaceholderText("File type analysis will appear here...")
        preview_layout.addWidget(self.file_types_text)

        left_layout.addWidget(preview_group)

        # Organization button
        self.organize_btn = QPushButton("🚀 Start Organization")
        self.organize_btn.clicked.connect(self.start_organization)
        self.organize_btn.setStyleSheet("QPushButton { background-color: #28a745; font-weight: bold; padding: 12px; font-size: 14px; }")
        self.organize_btn.setEnabled(False)
        left_layout.addWidget(self.organize_btn)

        left_layout.addStretch()
        left_panel.setMaximumWidth(380)

        # Center panel - File listing and preview
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # File listing tabs
        self.file_tabs = QTabWidget()

        # Source files tab
        source_tab = QWidget()
        source_layout = QVBoxLayout(source_tab)

        source_layout.addWidget(QLabel("Source Directory Contents:"))

        self.source_tree = QTreeWidget()
        self.source_tree.setHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.source_tree.itemClicked.connect(self.on_source_file_selected)
        source_layout.addWidget(self.source_tree)

        self.file_tabs.addTab(source_tab, "Source Files")

        # Organization preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)

        preview_layout.addWidget(QLabel("Organization Preview:"))

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Source", "Destination", "Action"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        preview_layout.addWidget(self.preview_table)

        self.file_tabs.addTab(preview_tab, "Preview")

        # History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        history_layout.addWidget(QLabel("Organization History:"))

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        history_layout.addWidget(self.history_list)

        self.file_tabs.addTab(history_tab, "History")

        center_layout.addWidget(self.file_tabs)

        # Right panel - Progress and results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Progress section
        progress_group = QGroupBox("Organization Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_status = QLabel("Ready")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status)

        # Progress details
        self.progress_details = QTextEdit()
        self.progress_details.setReadOnly(True)
        self.progress_details.setMaximumHeight(150)
        self.progress_details.setFont(QFont("Consolas", 9))
        progress_layout.addWidget(self.progress_details)

        right_layout.addWidget(progress_group)

        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        results_layout.addWidget(self.results_text)

        # Action buttons
        actions_layout = QHBoxLayout()

        open_output_btn = QPushButton("📁 Open Output")
        open_output_btn.clicked.connect(self.open_output_directory)
        actions_layout.addWidget(open_output_btn)

        export_report_btn = QPushButton("📊 Export Report")
        export_report_btn.clicked.connect(self.export_report)
        actions_layout.addWidget(export_report_btn)

        actions_layout.addStretch()

        results_layout.addLayout(actions_layout)
        right_layout.addWidget(results_group)

        right_panel.setMaximumWidth(400)

        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([380, 600, 400])

        layout.addWidget(main_splitter)

        # Status bar for this tab
        status_layout = QHBoxLayout()
        self.tab_status = QLabel("Ready")
        self.tab_indicator = QPushButton("●")
        self.tab_indicator.setStyleSheet("QPushButton { background-color: green; border-radius: 5px; max-width: 10px; max-height: 10px; }")

        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.tab_status)
        status_layout.addStretch()
        status_layout.addWidget(self.tab_indicator)

        layout.addLayout(status_layout)

    def _setup_drag_drop(self):
        """Setup drag and drop functionality."""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self.source_directory = path
                    self.source_path_edit.setText(path)
                    self._analyze_source_directory()
                    break

    # Directory selection
    def select_source_directory(self):
        """Select source directory for organization."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Source Directory",
            self.source_directory or os.path.expanduser("~")
        )

        if directory:
            self.source_directory = directory
            self.source_path_edit.setText(directory)
            self._analyze_source_directory()
            self._update_organize_button_state()

    def select_output_directory(self):
        """Select output directory for organized files."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_directory or os.path.expanduser("~/Documents/Organized")
        )

        if directory:
            self.output_directory = directory
            self.output_path_edit.setText(directory)
            self._update_organize_button_state()

    def _analyze_source_directory(self):
        """Analyze the source directory and populate file information."""
        if not self.source_directory or not os.path.exists(self.source_directory):
            return

        try:
            # Collect file information
            if FILE_ORGANIZER_AVAILABLE:
                file_paths = collect_file_paths(self.source_directory)
                file_types = separate_files_by_type(file_paths)
            else:
                file_paths = []
                file_types = {}

            # Update file count
            self.file_count_label.setText(f"Found {len(file_paths)} files")

            # Update file types analysis
            if file_types:
                analysis = []
                for file_type, files in file_types.items():
                    analysis.append(f"{file_type}: {len(files)} files")
                self.file_types_text.setPlainText("\n".join(analysis))
            else:
                self.file_types_text.setPlainText("No files found or analyzer unavailable")

            # Populate source tree
            self._populate_source_tree()

            self.tab_status.setText(f"Analyzed: {len(file_paths)} files")

        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze directory:\n{str(e)}")
            self.tab_status.setText(f"Analysis error: {str(e)}")

    def _populate_source_tree(self):
        """Populate the source directory tree widget."""
        self.source_tree.clear()

        if not self.source_directory:
            return

        try:
            for root, dirs, files in os.walk(self.source_directory):
                # Limit depth for performance
                depth = root[len(self.source_directory):].count(os.sep)
                if depth > 3:
                    continue

                for file in files[:100]:  # Limit files shown for performance
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.source_directory)

                    try:
                        stat = os.stat(file_path)
                        size = f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.1f} MB"
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                        item = QTreeWidgetItem([
                            rel_path,
                            os.path.splitext(file)[1] or "No extension",
                            size,
                            modified
                        ])
                        item.setData(0, Qt.ItemDataRole.UserRole, file_path)
                        self.source_tree.addTopLevelItem(item)

                    except (OSError, PermissionError):
                        continue

        except Exception as e:
            print(f"Error populating source tree: {e}")

    def _update_organize_button_state(self):
        """Update the organize button state based on selected directories."""
        can_organize = (
            self.source_directory and
            os.path.exists(self.source_directory) and
            self.output_directory and
            os.path.exists(self.output_directory)
        )
        self.organize_btn.setEnabled(can_organize)

    # Organization functionality
    def quick_organize(self):
        """Quick organization with default settings."""
        if not self.source_directory:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory to Organize")
            if not directory:
                return
            self.source_directory = directory
            self.source_path_edit.setText(directory)

        if not self.output_directory:
            self.output_directory = os.path.join(os.path.dirname(self.source_directory), "Organized")
            self.output_path_edit.setText(self.output_directory)

        self.start_organization()

    def start_organization(self):
        """Start the file organization process."""
        if not self.source_directory or not self.output_directory:
            QMessageBox.warning(self, "Missing Directories", "Please select both source and output directories.")
            return

        if self.organization_worker and self.organization_worker.isRunning():
            QMessageBox.information(self, "Organization in Progress", "File organization is already running.")
            return

        # Get organization mode
        mode_id = self.mode_group.checkedId()
        modes = ["by_type", "by_date", "legal_only", "smart"]
        mode = modes[mode_id] if mode_id >= 0 else "by_type"

        # Get options
        options = {
            'preserve_structure': self.preserve_structure_check.isChecked(),
            'copy_files': self.copy_files_check.isChecked(),
            'process_subdirs': self.process_subdirs_check.isChecked(),
            'use_ai': self.use_ai_check.isChecked()
        }

        # Disable organize button
        self.organize_btn.setText("🔄 Organizing...")
        self.organize_btn.setEnabled(False)

        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_status.setText("Starting organization...")
        self.progress_details.clear()

        # Start worker thread
        self.organization_worker = FileOrganizationWorker(
            self.source_directory,
            self.output_directory,
            mode,
            options
        )
        self.organization_worker.progress_updated.connect(self.on_organization_progress)
        self.organization_worker.file_processed.connect(self.on_file_processed)
        self.organization_worker.organization_complete.connect(self.on_organization_complete)
        self.organization_worker.error_occurred.connect(self.on_organization_error)
        self.organization_worker.start()

    def on_organization_progress(self, progress: int, status: str):
        """Handle organization progress updates."""
        self.progress_bar.setValue(progress)
        self.progress_status.setText(status)

    def on_file_processed(self, source: str, destination: str):
        """Handle individual file processing updates."""
        details = self.progress_details.toPlainText()
        details += f"✓ {os.path.basename(source)} → {os.path.relpath(destination, self.output_directory)}\n"
        self.progress_details.setPlainText(details)

        # Auto-scroll to bottom
        cursor = self.progress_details.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.progress_details.setTextCursor(cursor)

    def on_organization_complete(self, results: dict):
        """Handle completed organization."""
        # Update results display
        results_text = f"""Organization Complete!

Mode: {results['mode'].replace('_', ' ').title()}
Total Files: {results['total_files']}
Files Processed: {results['processed']}
Output Directory: {results['output_path']}

Organization completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.results_text.setPlainText(results_text)

        # Add to history
        history_item = {
            'timestamp': datetime.now().isoformat(),
            'source': self.source_directory,
            'output': self.output_directory,
            'results': results
        }
        self.operation_history.append(history_item)
        self._update_history_list()

        # Re-enable button
        self.organize_btn.setText("🚀 Start Organization")
        self.organize_btn.setEnabled(True)

        # Update status
        self.tab_status.setText(f"Organized {results['processed']} files")
        self.progress_status.setText("Complete")

        # Emit signal for other tabs
        self.files_organized.emit([])  # Could include specific file list
        self.directory_processed.emit(results['output_path'])

        # Switch to results tab
        self.file_tabs.setCurrentIndex(1)

    def on_organization_error(self, error: str):
        """Handle organization errors."""
        QMessageBox.critical(self, "Organization Error", f"Failed to organize files:\n{error}")

        # Re-enable button
        self.organize_btn.setText("🚀 Start Organization")
        self.organize_btn.setEnabled(True)

        # Update status
        self.tab_status.setText(f"Error: {error}")
        self.progress_status.setText("Error occurred")
        self.progress_bar.setValue(0)

    def _update_history_list(self):
        """Update the history list widget."""
        self.history_list.clear()
        for item in self.operation_history:
            timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')
            results = item['results']
            text = f"{timestamp} - {results['mode']} - {results['processed']} files"

            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

    # Event handlers
    def on_source_file_selected(self, item: QTreeWidgetItem, column: int):
        """Handle source file selection."""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            # Could show file preview here
            self.tab_status.setText(f"Selected: {os.path.basename(file_path)}")

    def load_history_item(self, item: QListWidgetItem):
        """Load a historical organization operation."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            results = data['results']
            details = f"""Historical Organization:

Timestamp: {data['timestamp']}
Source: {data['source']}
Output: {data['output']}
Mode: {results['mode']}
Files Processed: {results['processed']}
Total Files: {results['total_files']}
"""
            self.results_text.setPlainText(details)

    # Action handlers
    def open_output_directory(self):
        """Open the output directory in file explorer."""
        if self.output_directory and os.path.exists(self.output_directory):
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == "Windows":
                    subprocess.Popen(f'explorer "{self.output_directory}"')
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", self.output_directory])
                else:  # Linux
                    subprocess.Popen(["xdg-open", self.output_directory])

                self.tab_status.setText("Opened output directory")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open directory:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No Directory", "No output directory available.")

    def export_report(self):
        """Export organization report."""
        if not self.operation_history:
            QMessageBox.warning(self, "No Data", "No organization history to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Organization Report",
            f"organization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.operation_history, f, indent=2)
                self.tab_status.setText(f"Report exported: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{str(e)}")

    # Tab interface methods
    def initialize(self):
        """Initialize the tab when the application starts."""
        if FILE_ORGANIZER_AVAILABLE:
            self.tab_status.setText("File Organizer ready")
        else:
            self.tab_status.setText("File Organizer unavailable - demo mode")
            self.organize_btn.setEnabled(False)

    def on_activated(self):
        """Called when this tab becomes active."""
        self.tab_status.setText("File Organizer active")

    def cleanup(self):
        """Cleanup when application closes."""
        if self.organization_worker and self.organization_worker.isRunning():
            self.organization_worker.stop()
            self.organization_worker.wait()
