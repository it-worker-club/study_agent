"""Logging configuration for the education tutoring system"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    This formatter is useful for log aggregation systems and provides
    machine-readable log output with consistent structure.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """
    Filter that adds contextual information to log records.
    
    This filter can add custom fields like user_id, conversation_id, etc.
    to all log records for better traceability.
    """
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the context filter.
        
        Args:
            context: Dictionary of context fields to add to logs
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context fields to the log record.
        
        Args:
            record: Log record to modify
        
        Returns:
            True (always allow the record)
        """
        if not hasattr(record, "extra_fields"):
            record.extra_fields = {}
        
        record.extra_fields.update(self.context)
        return True


def setup_logger(
    name: str = "education_tutoring_system",
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    max_file_size: int = 10,
    backup_count: int = 5,
    structured: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format string (ignored if structured=True)
        log_file: Path to log file (None for console only)
        max_file_size: Maximum log file size in MB
        backup_count: Number of backup log files to keep
        structured: Use structured JSON logging format
        context: Context fields to add to all log records
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Choose formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        # Default format
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add context filter if provided
    if context:
        context_filter = ContextFilter(context)
        logger.addFilter(context_filter)
    
    return logger


def get_logger(name: str = "education_tutoring_system") -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def add_context_to_logger(logger: logging.Logger, context: Dict[str, Any]):
    """
    Add contextual information to a logger.
    
    This function adds a context filter to the logger that will include
    the specified context fields in all subsequent log records.
    
    Args:
        logger: Logger to modify
        context: Context fields to add
    
    Example:
        >>> logger = get_logger()
        >>> add_context_to_logger(logger, {"user_id": "user123", "conversation_id": "conv456"})
        >>> logger.info("Processing request")  # Will include user_id and conversation_id
    """
    context_filter = ContextFilter(context)
    logger.addFilter(context_filter)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger to use
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        context: Additional context fields
    
    Example:
        >>> logger = get_logger()
        >>> log_with_context(
        ...     logger,
        ...     "info",
        ...     "User action completed",
        ...     {"user_id": "user123", "action": "course_search"}
        ... )
    """
    log_func = getattr(logger, level.lower())
    
    if context:
        # Create a log record with extra fields
        extra = {"extra_fields": context}
        log_func(message, extra=extra)
    else:
        log_func(message)

