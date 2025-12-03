"""Logging configuration with rich output"""

import logging
import sys
from typing import Optional

try:
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging with optional rich output.
    
    Args:
        verbose: Enable DEBUG level logging
        log_file: Optional file path for logging output
    
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if RICH_AVAILABLE:
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=verbose,
            show_path=verbose
        )
        console_format = "%(message)s"
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = "%(levelname)s: %(message)s"
        if verbose:
            console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug for file
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        root_logger.addHandler(file_handler)
    
    # Return named logger
    logger = logging.getLogger("gitops-health")
    logger.setLevel(level)
    
    return logger


def get_logger(name: str = "gitops-health") -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
