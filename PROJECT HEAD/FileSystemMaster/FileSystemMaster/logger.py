"""
Logging configuration for the file automation tool
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Default log file with timestamp
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"file_automation_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Log startup info
    logger.info("=" * 50)
    logger.info("File Automation Tool - Starting")
    logger.info("=" * 50)
    logger.info(f"Log level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")
    
    return logger

def get_file_logger(name: str) -> logging.Logger:
    """Get a named logger for specific modules"""
    return logging.getLogger(name)

class ProgressLogger:
    """Progress logging utility for batch operations"""
    
    def __init__(self, total_items: int, logger: logging.Logger = None):
        self.total_items = total_items
        self.current_item = 0
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = datetime.now()
        
        # Progress reporting intervals
        self.report_intervals = [10, 25, 50, 75, 90, 95]
        self.last_reported = 0
    
    def update(self, increment: int = 1, message: str = None):
        """Update progress and log if necessary"""
        
        self.current_item += increment
        progress_percent = (self.current_item / self.total_items) * 100
        
        # Check if we should report progress
        should_report = False
        for interval in self.report_intervals:
            if progress_percent >= interval and self.last_reported < interval:
                should_report = True
                self.last_reported = interval
                break
        
        if should_report or self.current_item == self.total_items:
            elapsed = datetime.now() - self.start_time
            items_per_second = self.current_item / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            
            if self.current_item < self.total_items:
                remaining_items = self.total_items - self.current_item
                eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
                eta_str = f" (ETA: {int(eta_seconds)}s)" if eta_seconds > 0 else ""
            else:
                eta_str = ""
            
            log_message = f"Progress: {self.current_item}/{self.total_items} ({progress_percent:.1f}%){eta_str}"
            if message:
                log_message += f" - {message}"
            
            self.logger.info(log_message)
    
    def finish(self, message: str = "Processing complete"):
        """Log completion"""
        elapsed = datetime.now() - self.start_time
        self.logger.info(f"{message} - Total time: {elapsed.total_seconds():.1f}s")
