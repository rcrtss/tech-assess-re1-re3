"""
Shared logging configuration for the listener module.

This module provides a unified logging setup to ensure consistency across
the listener service. Follows the convention of minimal docstrings and
self-explanatory code as per DEVS.md.
"""

import logging
import sys
from typing import Optional


def configure_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__ of the calling module).
        level: Logging level (default: INFO).
        log_file: Optional file path to write logs to (default: None, logs to stderr).
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates.
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler (stderr).
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified.
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning(f"Could not open log file {log_file}: {e}")
    
    return logger
