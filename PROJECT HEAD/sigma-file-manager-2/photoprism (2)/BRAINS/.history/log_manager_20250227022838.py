#!/usr/bin/env python
"""
Centralized Logging System for Sorting Hat

This module provides a unified logging interface for all Sorting Hat components.
It handles log rotation, multiple output formats, and log file management.
"""
import os
import sys
import time
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, List, Any
import datetime
import json
import threading
import queue

# Singleton lock to ensure thread safety
_lock = threading.RLock()
_log_manager = None

# Configuration constants
MAX_LOG_SIZE_MB = 10
LOG_BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = logging.INFO

class LogManager:
    """Manages centralized logging for all Sorting Hat components"""
    
    def __init__(self):
        """Initialize the logging system with default configuration"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Main log files
        self.main_log_file = os.path.join(self.logs_dir, 'sorting_hat.log')
        self.error_log_file = os.path.join(self.logs_dir, 'error.log')
        self.access_log_file = os.path.join(self.logs_dir, 'access.log')
        
        # Setup main logger
        self._setup_main_logger()
        
        # Log message queue for live viewing
        self.log_queue = queue.Queue(maxsize=1000)  # Store last 1000 log messages
        
        # Store component loggers
        self.component_loggers = {}
        
        logging.info("Log Manager initialized")
    
    def _setup_main_logger(self):
        """Configure the root logger with handlers for console and file output"""
        # Reset root logger
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Configure logging level and format
        logging.basicConfig(
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        
        # Add handlers for different output types
        
        # 1. Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.root.addHandler(console_handler)
        
        # 2. Main log file with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.main_log_file,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.root.addHandler(file_handler)
        
        # 3. Error log file (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.root.addHandler(error_handler)
        
        # 4. Queue handler for live viewing
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.root.addHandler(queue_handler)
    
    def get_component_logger(self, component_name: str, log_to_separate_file: bool = False) -> logging.Logger:
        """Get a logger for a specific component
        
        Args:
            component_name: The name of the component (e.g. 'scheduler', 'watcher')
            log_to_separate_file: Whether to also log to a component-specific file
            
        Returns:
            A configured logger for the component
        """
        if component_name in self.component_loggers:
            return self.component_loggers[component_name]
            
        # Create a logger for this component
        logger = logging.getLogger(component_name)
        
        # If requested, add a component-specific log file
        if log_to_separate_file:
            component_log_file = os.path.join(self.logs_dir, f"{component_name}.log")
            handler = logging.handlers.RotatingFileHandler(
                component_log_file,
                maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=LOG_BACKUP_COUNT
            )
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
        
        # Store and return the logger
        self.component_loggers[component_name] = logger
        return logger
    
    def get_recent_logs(self, count: int = 100, level: int = logging.INFO, component: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries for viewing
        
        Args:
            count: Maximum number of log entries to return
            level: Minimum log level to include
            component: Optional component name to filter by
            
        Returns:
            List of log entries as dictionaries
        """
        # Convert queue to list without modifying the queue
        logs = []
        with _lock:
            # Get all items from queue without removing them
            items = list(self.log_queue.queue)
            
            # Filter and format logs
            for record in items:
                if record.levelno >= level and (component is None or record.name == component):
                    logs.append({
                        'timestamp': datetime.datetime.fromtimestamp(record.created).strftime(LOG_DATE_FORMAT),
                        'level': record.levelname,
                        'component': record.name,
                        'message': record.getMessage()
                    })
        
        # Return the most recent entries (up to count)
        return logs[-count:] if count < len(logs) else logs
    
    def get_log_tail(self, log_file: Optional[str] = None, lines: int = 100) -> List[str]:
        """Get the tail of a log file
        
        Args:
            log_file: Name of the log file to read (or None for main log)
            lines: Number of lines to read from the end
            
        Returns:
            List of log lines
        """
        if log_file is None:
            file_path = self.main_log_file
        elif log_file in ('error', 'access'):
            file_path = self.error_log_file if log_file == 'error' else self.access_log_file
        else:
            file_path = os.path.join(self.logs_dir, f"{log_file}.log")
            
        if not os.path.exists(file_path):
            return [f"Log file not found: {file_path}"]
            
        try:
            # This is a simple implementation that reads the whole file
            # For large files, a more efficient approach would be needed
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return list(f.readlines())[-lines:]
        except Exception as e:
            return [f"Error reading log file: {e}"]
    
    def export_logs(self, start_date: Optional[datetime.datetime] = None, 
                    end_date: Optional[datetime.datetime] = None) -> str:
        """Export logs to a JSON file for archiving or analysis
        
        Args:
            start_date: Start date for log export (or None for all)
            end_date: End date for log export (or None for all)
            
        Returns:
            Path to the exported log file
        """
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = os.path.join(self.logs_dir, f"logs_export_{timestamp}.json")
        
        # Process log files
        log_files = [f for f in os.listdir(self.logs_dir) if f.endswith('.log')]
        
        all_logs = []
        for log_file in log_files:
            file_path = os.path.join(self.logs_dir, log_file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        # Parse log line to extract timestamp
                        timestamp_str = line.split(' - ', 1)[0].strip()
                        log_time = datetime.datetime.strptime(timestamp_str, LOG_DATE_FORMAT)
                        
                        # Filter by date if specified
                        if (start_date is None or log_time >= start_date) and \
                           (end_date is None or log_time <= end_date):
                            all_logs.append(line.strip())
                    except:
                        # If parsing fails, include the line anyway
                        all_logs.append(line.strip())
        
        # Write to export file
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump({
                'exported_at': datetime.datetime.now().isoformat(),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'logs': all_logs
            }, f, indent=2)
            
        return export_file
    
    def clear_logs(self, days_to_keep: int = 7):
        """Clear old log files but keep recent logs
        
        Args:
            days_to_keep: Number of days worth of logs to keep
        """
        threshold = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        
        # Find all backup log files
        log_files = [f for f in os.listdir(self.logs_dir) if f.endswith('.log.1')]
        for file_name in log_files:
            file_path = os.path.join(self.logs_dir, file_name)
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Delete old files
            if file_time < threshold:
                try:
                    os.remove(file_path)
                    logging.info(f"Deleted old log file: {file_name}")
                except Exception as e:
                    logging.error(f"Failed to delete old log file {file_name}: {e}")

class QueueHandler(logging.Handler):
    """Special handler that puts logs into a queue for live viewing"""
    
    def __init__(self, log_queue: queue.Queue):
        """Initialize with a queue to store log records"""
        super().__init__()
        self.log_queue = log_queue
        
    def emit(self, record):
        """Add the log record to the queue, removing oldest if full"""
        try:
            # If queue is full, remove oldest item
            if self.log_queue.full():
                try:
                    self.log_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Add new record
            self.log_queue.put_nowait(record)
        except Exception:
            self.handleError(record)

def get_log_manager() -> LogManager:
    """Get or create the singleton LogManager instance"""
    global _log_manager
    with _lock:
        if _log_manager is None:
            _log_manager = LogManager()
        return _log_manager

def get_logger(component_name: str, separate_file: bool = False) -> logging.Logger:
    """Convenience function to get a logger for a component
    
    Args:
        component_name: The name of the component
        separate_file: Whether to also log to a component-specific file
        
    Returns:
        A configured logger for the component
    """
    manager = get_log_manager()
    return manager.get_component_logger(component_name, separate_file)

# Initialize on import
get_log_manager()
