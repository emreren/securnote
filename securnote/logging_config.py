"""
Logging configuration for SecurNote
Container-friendly logging setup
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level="INFO", log_file=None):
    """Setup logging configuration for SecurNote."""

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler (for container logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # SecurNote specific loggers
    loggers = {
        "securnote.auth": logging.getLogger("securnote.auth"),
        "securnote.crypto": logging.getLogger("securnote.crypto"),
        "securnote.web": logging.getLogger("securnote.web"),
        "securnote.admin": logging.getLogger("securnote.admin"),
        "securnote.storage": logging.getLogger("securnote.storage"),
    }

    # Set levels for specific modules
    for logger_name, logger in loggers.items():
        logger.setLevel(getattr(logging, log_level.upper()))

    logging.info("Logging configured successfully")
    return loggers


def get_logger(name):
    """Get logger for specific module."""
    return logging.getLogger(f"securnote.{name}")


# Container environment detection
def is_container():
    """Detect if running in container."""
    import os

    return Path("/.dockerenv").exists() or "KUBERNETES_SERVICE_HOST" in os.environ


# Default setup for imports
if __name__ != "__main__":
    import os

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", None)

    # In container, always log to stdout
    if is_container():
        log_file = None

    setup_logging(log_level, log_file)
