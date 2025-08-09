"""
SIGMA FILEBOSS - Unified Tabbed GUI Interface
Version: v1.0.0
Author: CURSOR PRIME
Purpose: Comprehensive file management system with integrated AI processing
Last Edited: 2025-01-27

Main application window that combines all FILEBOSS components into a unified interface.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMenuBar, QStatusBar, QToolBar,
    QMessageBox, QSplashScreen, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap, QFont

# Import our component tabs
from tabs.casebuilder_tab import CaseBuilderTab
from tabs.document_generator_tab import DocumentGeneratorTab
from tabs.whisperx_tab import WhisperXTab
from tabs.file_organizer_tab import FileOrganizerTab
from tabs.photoprism_tab import PhotoPrismTab
from tabs.legal_brain_tab import LegalBrainTab
from tabs.ai_analysis_tab import AIAnalysisTab
from tabs.system_monitor_tab import SystemMonitorTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fileboss.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SigmaFileBossMainWindow(QMainWindow):
    """Main application window for Sigma FileBoss unified interface."""

    def __init__(self):
        super().__init__()

        # Application state
        self.current_session = None
        self.active_processes = []

        # Initialize UI
        self.setWindowTitle("SIGMA FILEBOSS - Unified File Management & AI Processing Suite")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # Apply modern styling
        self._apply_modern_theme()

        # Setup UI components
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()

        # Initialize components
        self._initialize_components()

        logger.info("SIGMA FILEBOSS Main Window initialized successfully")

    def _apply_modern_theme(self):
        """Apply modern dark theme styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QMenuBar {
                background-color: #333333;
                color: #ffffff;
                border: none;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #404040;
                border: none;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #333333;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)

    def _create_actions(self):
        """Create actions for menus and toolbars."""
        # File actions
        self.new_session_action = QAction("&New Session", self)
        self.new_session_action.setShortcut("Ctrl+N")
        self.new_session_action.triggered.connect(self.new_session)

        self.save_session_action = QAction("&Save Session", self)
        self.save_session_action.setShortcut("Ctrl+S")
        self.save_session_action.triggered.connect(self.save_session)

        self.load_session_action = QAction("&Load Session", self)
        self.load_session_action.setShortcut("Ctrl+O")
        self.load_session_action.triggered.connect(self.load_session)

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.triggered.connect(self.close)

        # Tools actions
        self.system_check_action = QAction("System &Check", self)
        self.system_check_action.triggered.connect(self.run_system_check)

        self.preferences_action = QAction("&Preferences", self)
        self.preferences_action.triggered.connect(self.show_preferences)

        # Help actions
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about)

        self.documentation_action = QAction("&Documentation", self)
        self.documentation_action.triggered.connect(self.show_documentation)

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.new_session_action)
        file_menu.addAction(self.save_session_action)
        file_menu.addAction(self.load_session_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.system_check_action)
        tools_menu.addAction(self.preferences_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.about_action)
        help_menu.addAction(self.documentation_action)

    def _create_tool_bar(self):
        """Create the main toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # Add commonly used actions
        toolbar.addAction(self.new_session_action)
        toolbar.addAction(self.save_session_action)
        toolbar.addAction(self.load_session_action)
        toolbar.addSeparator()
        toolbar.addAction(self.system_check_action)

        # Add quick access buttons
        quick_organize_btn = QPushButton("Quick Organize")
        quick_organize_btn.clicked.connect(self.quick_organize)
        toolbar.addWidget(quick_organize_btn)

        ai_analyze_btn = QPushButton("AI Analyze")
        ai_analyze_btn.clicked.connect(self.quick_ai_analyze)
        toolbar.addWidget(ai_analyze_btn)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status widgets
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)

        # System status indicators
        self.db_status = QLabel("DB: ●")
        self.db_status.setStyleSheet("color: green;")

        self.ai_status = QLabel("AI: ●")
        self.ai_status.setStyleSheet("color: green;")

        # Add to status bar
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.db_status)
        self.status_bar.addPermanentWidget(self.ai_status)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def _create_central_widget(self):
        """Create the main tabbed interface."""
        # Create central tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)

        # Add tabs - order matters for user workflow
        self.tabs = {}

        # Tab 1: Case Builder (Main file management)
        self.tabs['casebuilder'] = CaseBuilderTab()
        self.tab_widget.addTab(self.tabs['casebuilder'], "📁 Case Builder")

        # Tab 2: Document Generator
        self.tabs['docgen'] = DocumentGeneratorTab()
        self.tab_widget.addTab(self.tabs['docgen'], "📝 Document Generator")

        # Tab 3: WhisperX (Audio Processing)
        self.tabs['whisperx'] = WhisperXTab()
        self.tab_widget.addTab(self.tabs['whisperx'], "🎤 WhisperX Audio")

        # Tab 4: File Organizer
        self.tabs['organizer'] = FileOrganizerTab()
        self.tab_widget.addTab(self.tabs['organizer'], "🗂️ File Organizer")

        # Tab 5: PhotoPrism Integration
        self.tabs['photoprism'] = PhotoPrismTab()
        self.tab_widget.addTab(self.tabs['photoprism'], "📸 PhotoPrism")

        # Tab 6: Legal Brain (Advanced Processing)
        self.tabs['legal'] = LegalBrainTab()
        self.tab_widget.addTab(self.tabs['legal'], "⚖️ Legal Brain")

        # Tab 7: AI Analysis
        self.tabs['ai'] = AIAnalysisTab()
        self.tab_widget.addTab(self.tabs['ai'], "🧠 AI Analysis")

        # Tab 8: System Monitor
        self.tabs['monitor'] = SystemMonitorTab()
        self.tab_widget.addTab(self.tabs['monitor'], "📊 System Monitor")

        # Connect tab change events
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.setCentralWidget(self.tab_widget)

    def _initialize_components(self):
        """Initialize all component systems."""
        try:
            # Initialize each tab's components
            for tab_name, tab_widget in self.tabs.items():
                if hasattr(tab_widget, 'initialize'):
                    tab_widget.initialize()
                    logger.info(f"Initialized {tab_name} tab")

            # Setup cross-tab communication
            self._setup_tab_communication()

            # Start system monitoring
            self._start_system_monitoring()

            self.status_label.setText("All systems ready")

        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            QMessageBox.critical(self, "Initialization Error",
                               f"Failed to initialize some components: {str(e)}")

    def _setup_tab_communication(self):
        """Setup communication between tabs."""
        # Connect signals between tabs for data sharing
        # Case Builder -> other tabs
        if hasattr(self.tabs['casebuilder'], 'case_selected'):
            self.tabs['casebuilder'].case_selected.connect(
                self.tabs['legal'].load_case_data
            )
            self.tabs['casebuilder'].case_selected.connect(
                self.tabs['ai'].load_case_data
            )

        # File Organizer -> Case Builder
        if hasattr(self.tabs['organizer'], 'files_organized'):
            self.tabs['organizer'].files_organized.connect(
                self.tabs['casebuilder'].refresh_files
            )

        # WhisperX -> Legal Brain
        if hasattr(self.tabs['whisperx'], 'transcription_complete'):
            self.tabs['whisperx'].transcription_complete.connect(
                self.tabs['legal'].process_transcription
            )

    def _start_system_monitoring(self):
        """Start background system monitoring."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_system_status)
        self.monitor_timer.start(5000)  # Update every 5 seconds

    def _update_system_status(self):
        """Update system status indicators."""
        try:
            # Check database connection
            db_ok = self._check_database_status()
            self.db_status.setStyleSheet(f"color: {'green' if db_ok else 'red'};")

            # Check AI services
            ai_ok = self._check_ai_status()
            self.ai_status.setStyleSheet(f"color: {'green' if ai_ok else 'red'};")

        except Exception as e:
            logger.error(f"Error updating system status: {e}")

    def _check_database_status(self) -> bool:
        """Check database connectivity."""
        try:
            # Implement database health check
            return True  # Placeholder
        except:
            return False

    def _check_ai_status(self) -> bool:
        """Check AI services status."""
        try:
            # Implement AI services health check
            return True  # Placeholder
        except:
            return False

    # Event handlers
    def on_tab_changed(self, index: int):
        """Handle tab change events."""
        tab_name = list(self.tabs.keys())[index]
        logger.info(f"Switched to {tab_name} tab")

        # Update status bar
        self.status_label.setText(f"Active: {tab_name.title()}")

        # Notify the active tab
        active_tab = self.tabs[tab_name]
        if hasattr(active_tab, 'on_activated'):
            active_tab.on_activated()

    # Action handlers
    def new_session(self):
        """Create a new session."""
        # Implement session management
        self.status_label.setText("New session created")
        logger.info("New session created")

    def save_session(self):
        """Save current session."""
        # Implement session saving
        self.status_label.setText("Session saved")
        logger.info("Session saved")

    def load_session(self):
        """Load a saved session."""
        # Implement session loading
        self.status_label.setText("Session loaded")
        logger.info("Session loaded")

    def quick_organize(self):
        """Quick file organization."""
        self.tab_widget.setCurrentWidget(self.tabs['organizer'])
        if hasattr(self.tabs['organizer'], 'quick_organize'):
            self.tabs['organizer'].quick_organize()

    def quick_ai_analyze(self):
        """Quick AI analysis."""
        self.tab_widget.setCurrentWidget(self.tabs['ai'])
        if hasattr(self.tabs['ai'], 'quick_analyze'):
            self.tabs['ai'].quick_analyze()

    def run_system_check(self):
        """Run comprehensive system check."""
        self.tab_widget.setCurrentWidget(self.tabs['monitor'])
        if hasattr(self.tabs['monitor'], 'run_full_check'):
            self.tabs['monitor'].run_full_check()

    def show_preferences(self):
        """Show preferences dialog."""
        # Implement preferences dialog
        QMessageBox.information(self, "Preferences", "Preferences dialog not yet implemented")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SIGMA FILEBOSS",
            """<h2>SIGMA FILEBOSS v1.0.0</h2>
            <p><b>Unified File Management & AI Processing Suite</b></p>
            <p>© 2025 CURSOR PRIME Architecture</p>

            <p><b>Integrated Components:</b></p>
            <ul>
            <li>🗂️ Advanced File Organization</li>
            <li>⚖️ Legal Document Processing</li>
            <li>🎤 Audio Transcription (WhisperX)</li>
            <li>📸 Photo Management (PhotoPrism)</li>
            <li>🧠 AI-Powered Analysis</li>
            <li>📊 System Monitoring</li>
            </ul>

            <p><b>Built with:</b> PyQt6, SQLAlchemy, FastAPI, Docker</p>
            """
        )

    def show_documentation(self):
        """Show documentation."""
        # Implement documentation viewer
        QMessageBox.information(self, "Documentation", "Documentation viewer not yet implemented")

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Stop monitoring
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()

            # Cleanup tabs
            for tab_name, tab_widget in self.tabs.items():
                if hasattr(tab_widget, 'cleanup'):
                    tab_widget.cleanup()

            logger.info("SIGMA FILEBOSS shutdown complete")
            event.accept()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()


class SplashScreen(QSplashScreen):
    """Custom splash screen for application startup."""

    def __init__(self):
        # Create a simple splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.darkBlue)
        super().__init__(pixmap)

        # Add text
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.showMessage(
            "SIGMA FILEBOSS\nInitializing...",
            Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.white
        )


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("SIGMA FILEBOSS")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CURSOR PRIME")

    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    try:
        # Create and show main window
        window = SigmaFileBossMainWindow()

        # Hide splash and show main window
        splash.finish(window)
        window.show()

        # Start application event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Critical error starting application: {e}")
        QMessageBox.critical(None, "Startup Error", f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
