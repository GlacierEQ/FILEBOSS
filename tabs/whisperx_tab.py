"""
WhisperX Tab - Audio Transcription & Processing
Integrates the Legal Brain audio processing capabilities
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QFileDialog, QMessageBox,
    QSplitter, QFrame, QTabWidget, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QUrl
from PyQt6.QtGui import QFont, QTextCursor, QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# Import Legal Brain audio processor
sys.path.append(str(Path(__file__).parent.parent / "PROJECT HEAD/sigma-file-manager-2/photoprism (2)/Legal_brain"))
try:
    from audio_processor import AudioProcessor
    from config import Config
    WHISPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: WhisperX components not available: {e}")
    WHISPER_AVAILABLE = False

class AudioTranscriptionWorker(QThread):
    """Worker thread for audio transcription to prevent UI blocking."""

    progress_updated = pyqtSignal(int, str)  # progress, status
    transcription_complete = pyqtSignal(str, dict)  # text, metadata
    error_occurred = pyqtSignal(str)

    def __init__(self, audio_file_path: str, processor: 'AudioProcessor' = None):
        super().__init__()
        self.audio_file_path = audio_file_path
        self.processor = processor
        self.should_stop = False

    def run(self):
        """Run the transcription process."""
        try:
            if not self.processor:
                self.error_occurred.emit("Audio processor not available")
                return

            self.progress_updated.emit(10, "Initializing transcription...")

            # Transcribe the audio
            result = self.processor.transcribe_audio(self.audio_file_path)

            if self.should_stop:
                return

            self.progress_updated.emit(50, "Processing transcription...")

            if result and 'text' in result:
                # Extract metadata
                metadata = {
                    'file_path': self.audio_file_path,
                    'duration': result.get('duration', 0),
                    'language': result.get('language', 'unknown'),
                    'confidence': result.get('confidence', 0.0),
                    'segments': result.get('segments', [])
                }

                self.progress_updated.emit(100, "Transcription complete")
                self.transcription_complete.emit(result['text'], metadata)
            else:
                self.error_occurred.emit("No transcription result received")

        except Exception as e:
            self.error_occurred.emit(f"Transcription error: {str(e)}")

    def stop(self):
        """Stop the transcription process."""
        self.should_stop = True

class WhisperXTab(QWidget):
    """WhisperX audio transcription tab."""

    # Signals for cross-tab communication
    transcription_complete = pyqtSignal(str, dict)  # text, metadata
    audio_processed = pyqtSignal(str)  # file_path

    def __init__(self):
        super().__init__()

        # Initialize audio processor
        if WHISPER_AVAILABLE:
            try:
                self.audio_processor = AudioProcessor()
            except Exception as e:
                print(f"Error initializing AudioProcessor: {e}")
                self.audio_processor = None
        else:
            self.audio_processor = None

        # State variables
        self.current_audio_file = None
        self.transcription_worker = None
        self.transcription_history = []

        # Media player for audio playback
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self):
        """Setup the tab's user interface."""
        layout = QVBoxLayout(self)

        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("🎤 WhisperX - Audio Transcription & Processing")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Quick action buttons
        load_audio_btn = QPushButton("Load Audio File")
        load_audio_btn.clicked.connect(self.load_audio_file)
        header_layout.addWidget(load_audio_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header_frame)

        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Audio controls and settings
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Audio file info
        file_info_group = QGroupBox("Audio File Information")
        file_info_layout = QFormLayout(file_info_group)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_size_label = QLabel("-")
        self.file_duration_label = QLabel("-")
        self.file_format_label = QLabel("-")

        file_info_layout.addRow("File:", self.file_path_edit)
        file_info_layout.addRow("Size:", self.file_size_label)
        file_info_layout.addRow("Duration:", self.file_duration_label)
        file_info_layout.addRow("Format:", self.file_format_label)

        left_layout.addWidget(file_info_group)

        # Audio playback controls
        playback_group = QGroupBox("Audio Playback")
        playback_layout = QVBoxLayout(playback_group)

        # Play controls
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.pause_playback)
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_playback)

        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()

        playback_layout.addLayout(controls_layout)

        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)

        playback_layout.addLayout(volume_layout)

        left_layout.addWidget(playback_group)

        # Transcription settings
        settings_group = QGroupBox("Transcription Settings")
        settings_layout = QFormLayout(settings_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto-detect", "English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian", "Japanese", "Chinese"])

        self.model_combo = QComboBox()
        self.model_combo.addItems(["base", "small", "medium", "large"])

        self.timestamp_check = QCheckBox("Include timestamps")
        self.timestamp_check.setChecked(True)

        self.speaker_check = QCheckBox("Speaker diarization")
        self.speaker_check.setChecked(False)

        settings_layout.addRow("Language:", self.language_combo)
        settings_layout.addRow("Model:", self.model_combo)
        settings_layout.addRow("", self.timestamp_check)
        settings_layout.addRow("", self.speaker_check)

        # Transcription button
        self.transcribe_btn = QPushButton("🎯 Start Transcription")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setStyleSheet("QPushButton { background-color: #28a745; font-weight: bold; padding: 8px; }")
        settings_layout.addRow(self.transcribe_btn)

        left_layout.addWidget(settings_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_status = QLabel("Ready")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status)

        left_layout.addWidget(progress_group)
        left_layout.addStretch()
        left_panel.setMaximumWidth(350)

        # Right panel - Transcription results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Transcription tabs
        self.transcription_tabs = QTabWidget()

        # Current transcription tab
        current_tab = QWidget()
        current_layout = QVBoxLayout(current_tab)

        current_layout.addWidget(QLabel("Current Transcription:"))
        self.transcription_text = QTextEdit()
        self.transcription_text.setFont(QFont("Consolas", 10))
        self.transcription_text.setPlaceholderText("Transcribed text will appear here...")
        current_layout.addWidget(self.transcription_text)

        # Text editing tools
        text_tools = QHBoxLayout()

        save_btn = QPushButton("💾 Save Text")
        save_btn.clicked.connect(self.save_transcription)
        text_tools.addWidget(save_btn)

        copy_btn = QPushButton("📋 Copy Text")
        copy_btn.clicked.connect(self.copy_transcription)
        text_tools.addWidget(copy_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_transcription)
        text_tools.addWidget(export_btn)

        text_tools.addStretch()

        send_legal_btn = QPushButton("⚖️ Send to Legal Brain")
        send_legal_btn.clicked.connect(self.send_to_legal_brain)
        text_tools.addWidget(send_legal_btn)

        current_layout.addLayout(text_tools)

        self.transcription_tabs.addTab(current_tab, "Current")

        # History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        history_layout.addWidget(QLabel("Transcription History:"))
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_historical_transcription)
        history_layout.addWidget(self.history_list)

        self.transcription_tabs.addTab(history_tab, "History")

        # Metadata tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)

        metadata_layout.addWidget(QLabel("Audio & Transcription Metadata:"))
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setFont(QFont("Consolas", 9))
        metadata_layout.addWidget(self.metadata_text)

        self.transcription_tabs.addTab(metadata_tab, "Metadata")

        right_layout.addWidget(self.transcription_tabs)

        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 800])

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
            urls = event.mimeData().urls()
            if urls and any(url.toLocalFile().lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac')) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac')):
                    self.load_audio_file(file_path)
                    break

    # Audio file handling
    def load_audio_file(self, file_path: str = None):
        """Load an audio file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Audio File",
                "",
                "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg *.aac);;All Files (*)"
            )

        if file_path and os.path.exists(file_path):
            self.current_audio_file = file_path
            self._update_file_info(file_path)
            self._load_media_file(file_path)
            self.tab_status.setText(f"Loaded: {os.path.basename(file_path)}")

    def _update_file_info(self, file_path: str):
        """Update file information display."""
        try:
            file_stat = os.stat(file_path)
            file_size = f"{file_stat.st_size / (1024*1024):.1f} MB"

            self.file_path_edit.setText(file_path)
            self.file_size_label.setText(file_size)
            self.file_format_label.setText(os.path.splitext(file_path)[1].upper())

            # Try to get duration (simplified)
            self.file_duration_label.setText("Loading...")

        except Exception as e:
            print(f"Error updating file info: {e}")

    def _load_media_file(self, file_path: str):
        """Load file into media player."""
        try:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.tab_status.setText("Audio file loaded")
        except Exception as e:
            print(f"Error loading media file: {e}")

    # Playback controls
    def toggle_playback(self):
        """Toggle audio playback."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def pause_playback(self):
        """Pause audio playback."""
        self.media_player.pause()

    def stop_playback(self):
        """Stop audio playback."""
        self.media_player.stop()

    def set_volume(self, value: int):
        """Set playback volume."""
        self.audio_output.setVolume(value / 100.0)

    # Transcription functionality
    def start_transcription(self):
        """Start the transcription process."""
        if not self.current_audio_file:
            QMessageBox.warning(self, "No Audio File", "Please load an audio file first.")
            return

        if not self.audio_processor:
            QMessageBox.warning(self, "Service Unavailable", "WhisperX service is not available.")
            return

        if self.transcription_worker and self.transcription_worker.isRunning():
            QMessageBox.information(self, "Transcription in Progress", "A transcription is already running.")
            return

        # Disable transcription button
        self.transcribe_btn.setText("🔄 Transcribing...")
        self.transcribe_btn.setEnabled(False)

        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_status.setText("Starting transcription...")

        # Start worker thread
        self.transcription_worker = AudioTranscriptionWorker(
            self.current_audio_file,
            self.audio_processor
        )
        self.transcription_worker.progress_updated.connect(self.on_transcription_progress)
        self.transcription_worker.transcription_complete.connect(self.on_transcription_complete)
        self.transcription_worker.error_occurred.connect(self.on_transcription_error)
        self.transcription_worker.start()

    def on_transcription_progress(self, progress: int, status: str):
        """Handle transcription progress updates."""
        self.progress_bar.setValue(progress)
        self.progress_status.setText(status)

    def on_transcription_complete(self, text: str, metadata: dict):
        """Handle completed transcription."""
        # Update UI
        self.transcription_text.setPlainText(text)
        self.metadata_text.setPlainText(json.dumps(metadata, indent=2))

        # Add to history
        self.transcription_history.append({
            'file': os.path.basename(self.current_audio_file),
            'text': text,
            'metadata': metadata,
            'timestamp': metadata.get('timestamp', 'Unknown')
        })
        self._update_history_list()

        # Re-enable button
        self.transcribe_btn.setText("🎯 Start Transcription")
        self.transcribe_btn.setEnabled(True)

        # Update status
        self.tab_status.setText("Transcription complete")
        self.progress_status.setText("Complete")

        # Emit signal for other tabs
        self.transcription_complete.emit(text, metadata)

        # Switch to current transcription tab
        self.transcription_tabs.setCurrentIndex(0)

    def on_transcription_error(self, error: str):
        """Handle transcription errors."""
        QMessageBox.critical(self, "Transcription Error", f"Failed to transcribe audio:\n{error}")

        # Re-enable button
        self.transcribe_btn.setText("🎯 Start Transcription")
        self.transcribe_btn.setEnabled(True)

        # Update status
        self.tab_status.setText(f"Error: {error}")
        self.progress_status.setText("Error occurred")
        self.progress_bar.setValue(0)

    def _update_history_list(self):
        """Update the history list widget."""
        self.history_list.clear()
        for item in self.transcription_history:
            list_item = QListWidgetItem(f"{item['file']} - {item['timestamp']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

    def load_historical_transcription(self, item: QListWidgetItem):
        """Load a historical transcription."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.transcription_text.setPlainText(data['text'])
            self.metadata_text.setPlainText(json.dumps(data['metadata'], indent=2))
            self.transcription_tabs.setCurrentIndex(0)

    # Text operations
    def save_transcription(self):
        """Save the current transcription to file."""
        if not self.transcription_text.toPlainText().strip():
            QMessageBox.warning(self, "No Content", "No transcription to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Transcription",
            f"transcription_{os.path.splitext(os.path.basename(self.current_audio_file or 'audio'))[0]}.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.transcription_text.toPlainText())
                self.tab_status.setText(f"Saved: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def copy_transcription(self):
        """Copy transcription to clipboard."""
        text = self.transcription_text.toPlainText().strip()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.tab_status.setText("Transcription copied to clipboard")
        else:
            QMessageBox.warning(self, "No Content", "No transcription to copy.")

    def export_transcription(self):
        """Export transcription in various formats."""
        # Implementation for export functionality
        QMessageBox.information(self, "Export", "Export functionality not yet implemented")

    def send_to_legal_brain(self):
        """Send transcription to Legal Brain tab."""
        text = self.transcription_text.toPlainText().strip()
        if text:
            # Signal to legal brain tab
            QMessageBox.information(self, "Legal Brain", "Sending transcription to Legal Brain tab...")
        else:
            QMessageBox.warning(self, "No Content", "No transcription to send.")

    def clear_all(self):
        """Clear all content."""
        self.transcription_text.clear()
        self.metadata_text.clear()
        self.current_audio_file = None
        self.file_path_edit.clear()
        self.file_size_label.setText("-")
        self.file_duration_label.setText("-")
        self.file_format_label.setText("-")
        self.progress_bar.setValue(0)
        self.progress_status.setText("Ready")
        self.tab_status.setText("Cleared")

    # Tab interface methods
    def initialize(self):
        """Initialize the tab when the application starts."""
        if WHISPER_AVAILABLE:
            self.tab_status.setText("WhisperX ready")
        else:
            self.tab_status.setText("WhisperX unavailable - demo mode")
            self.transcribe_btn.setEnabled(False)

    def on_activated(self):
        """Called when this tab becomes active."""
        self.tab_status.setText("WhisperX active")

    def cleanup(self):
        """Cleanup when application closes."""
        if self.transcription_worker and self.transcription_worker.isRunning():
            self.transcription_worker.stop()
            self.transcription_worker.wait()

        self.media_player.stop()
