""
GUI Utilities

This module provides utility functions for the FileBoss GUI.
"""

import os
import logging
from typing import Any, Callable, Optional, TypeVar, Type, Tuple, Dict
from functools import wraps
from pathlib import Path

from PyQt6.QtWidgets import (
    QMessageBox, QProgressDialog, QFileDialog, QInputDialog, QWidget
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QObject, QRunnable, QThreadPool

# Type variable for generic type hints
T = TypeVar('T')

def handle_errors(show_dialog: bool = True, default_return: Any = None):
    """
    Decorator to handle errors in GUI methods.
    
    Args:
        show_dialog: Whether to show an error dialog on exception
        default_return: Value to return on exception
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                
                # Only show dialog if requested and if we have a QApplication
                if show_dialog and QApplication.instance() is not None:
                    parent = None
                    if args and isinstance(args[0], QWidget):
                        parent = args[0]
                    
                    QMessageBox.critical(
                        parent,
                        "Error",
                        f"An error occurred in {func.__name__}:\n\n{str(e)}"
                    )
                
                return default_return
        return wrapper
    return decorator


def show_busy_cursor(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to show busy cursor during function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            return func(*args, **kwargs)
        finally:
            QApplication.restoreOverrideCursor()
    return wrapper


def confirm_action(
    parent: QWidget,
    title: str,
    message: str,
    detailed_text: str = "",
    buttons: QMessageBox.StandardButtons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.No
) -> bool:
    """
    Show a confirmation dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Message text
        detailed_text: Additional detailed text (optional)
        buttons: Buttons to show
        default_button: Default button
        
    Returns:
        True if user confirmed, False otherwise
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    
    result = msg_box.exec()
    return result == QMessageBox.StandardButton.Yes


def show_error(
    parent: QWidget,
    title: str,
    message: str,
    detailed_text: str = ""
) -> None:
    """Show an error message dialog."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    
    msg_box.exec()


def show_info(
    parent: QWidget,
    title: str,
    message: str,
    detailed_text: str = ""
) -> None:
    """Show an information message dialog."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    
    msg_box.exec()


def show_warning(
    parent: QWidget,
    title: str,
    message: str,
    detailed_text: str = ""
) -> None:
    """Show a warning message dialog."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    
    msg_box.exec()


def get_open_file_names(
    parent: QWidget,
    caption: str = "Open Files",
    directory: str = "",
    filter: str = "All Files (*)",
    selected_filter: str = "",
    options: QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog
) -> Tuple[list, str]:
    """Show a file open dialog and return selected files and selected filter."""
    dialog = QFileDialog(parent, caption, directory, filter)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setOptions(options)
    
    if selected_filter:
        dialog.selectNameFilter(selected_filter)
    
    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        return dialog.selectedFiles(), dialog.selectedNameFilter()
    
    return [], ""


def get_existing_directory(
    parent: QWidget = None,
    caption: str = "Select Directory",
    directory: str = "",
    options: QFileDialog.Option = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
) -> str:
    """Show a directory selection dialog and return the selected directory."""
    return QFileDialog.getExistingDirectory(
        parent=parent,
        caption=caption,
        directory=directory,
        options=options
    )


def get_save_file_name(
    parent: QWidget = None,
    caption: str = "Save File",
    directory: str = "",
    filter: str = "All Files (*)",
    selected_filter: str = "",
    options: QFileDialog.Option = QFileDialog.Option.DontUseNativeDialog
) -> Tuple[str, str]:
    """Show a file save dialog and return the selected file and filter."""
    dialog = QFileDialog(parent, caption, directory, filter)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setOptions(options)
    
    if selected_filter:
        dialog.selectNameFilter(selected_filter)
    
    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        files = dialog.selectedFiles()
        if files:
            return files[0], dialog.selectedNameFilter()
    
    return "", ""


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int, str)


class Worker(QRunnable):
    """
    Worker thread for running background tasks.
    
    Example:
        worker = Worker(my_long_running_function, arg1, arg2, ...)
        worker.signals.result.connect(self.handle_result)
        worker.signals.finished.connect(self.task_complete)
        worker.signals.progress.connect(self.update_progress)
        QThreadPool.globalInstance().start(worker)
    """
    
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Add progress callback to kwargs if the function accepts it
        if 'progress_callback' in self.kwargs:
            self.kwargs['progress_callback'] = self.signals.progress.emit
    
    @handle_errors()
    def run(self):
        """Run the worker function."""
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit((type(e), e, e.__traceback__))
        finally:
            self.signals.finished.emit()


def run_in_background(
    fn: Callable,
    on_result: Callable[[Any], None] = None,
    on_error: Callable[[Exception], None] = None,
    on_finished: Callable[[], None] = None,
    on_progress: Callable[[int, str], None] = None,
    *args, **kwargs
) -> Worker:
    """
    Run a function in a background thread.
    
    Args:
        fn: Function to run in the background
        on_result: Callback for when the function completes successfully
        on_error: Callback for when an error occurs
        on_finished: Callback for when the thread finishes (always called)
        on_progress: Callback for progress updates (progress_callback will be passed to fn)
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The worker thread
    """
    worker = Worker(fn, *args, **kwargs)
    
    if on_result is not None:
        worker.signals.result.connect(on_result)
    
    if on_error is not None:
        worker.signals.error.connect(lambda e: on_error(e[1]))
    
    if on_finished is not None:
        worker.signals.finished.connect(on_finished)
    
    if on_progress is not None:
        worker.signals.progress.connect(on_progress)
    
    QThreadPool.globalInstance().start(worker)
    return worker
