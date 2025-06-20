#!/usr/bin/env python3
"""
Logging Utilities

This module provides utilities for setting up logging across the LogSentinel project.
"""

import logging

def setup_logger(logger_name=None, log_level="INFO"):
    """Configure logging for the module.

    Args:
        logger_name: Name of the logger (default: caller's module name)
        log_level: The logging level to use (default: INFO)

    Returns:
        Logger: Configured logger instance
    """
    # Use provided logger name or get the caller's module name
    logger = logging.getLogger(logger_name if logger_name else __name__)

    # Define logging levels
    levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET
    }

    # Check if logger already has handlers to avoid duplicates
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s.%(funcName)s   --->   %(message)s')
        handler.setFormatter(formatter)

        logger.setLevel(levels.get(log_level, "INFO"))
        logger.addHandler(handler)

        # Avoid duplicate log messages
        logger.propagate = False

    return logger
