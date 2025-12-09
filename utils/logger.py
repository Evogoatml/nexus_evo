"""
Structured logging for nexus_evo
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class NexusLogger:
    """Custom logger for nexus_evo with structured output"""
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, **kwargs):
        extra = f" | {kwargs}" if kwargs else ""
        self.logger.debug(f"{msg}{extra}")
    
    def info(self, msg: str, **kwargs):
        extra = f" | {kwargs}" if kwargs else ""
        self.logger.info(f"{msg}{extra}")
    
    def warning(self, msg: str, **kwargs):
        extra = f" | {kwargs}" if kwargs else ""
        self.logger.warning(f"{msg}{extra}")
    
    def error(self, msg: str, **kwargs):
        extra = f" | {kwargs}" if kwargs else ""
        self.logger.error(f"{msg}{extra}")
    
    def critical(self, msg: str, **kwargs):
        extra = f" | {kwargs}" if kwargs else ""
        self.logger.critical(f"{msg}{extra}")


def get_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> NexusLogger:
    """Get or create a logger instance"""
    return NexusLogger(name, log_file, level)
