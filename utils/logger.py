"""
Structured logging configuration for the Financial Chatbot RAG System.

This module provides centralized logging configuration with:
- Daily log file rotation
- Structured log formatting with timestamps and context
- Different log levels for console and file output
- Request/response logging utilities
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log messages.
    
    Format: [timestamp] [level] [component] message {context}
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with structured information.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string
        """
        # Base format
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        component = record.name
        message = record.getMessage()
        
        # Build base log string
        log_parts = [
            f"[{timestamp}]",
            f"[{level}]",
            f"[{component}]",
            message
        ]
        
        # Add context if available
        context = {}
        
        # Add exception info if present
        if record.exc_info:
            context['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields from the record
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'taskName'
            ]
        }
        
        if extra_fields:
            context.update(extra_fields)
        
        # Append context if present
        if context:
            try:
                context_str = json.dumps(context, default=str)
                log_parts.append(context_str)
            except Exception:
                # Fallback if JSON serialization fails
                log_parts.append(str(context))
        
        return " ".join(log_parts)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    log_file: str = "app.log",
    console_level: Optional[str] = None
) -> None:
    """
    Configure application-wide logging with file rotation and structured formatting.
    
    Sets up:
    - Console handler with configurable level
    - File handler with daily rotation
    - Structured log formatting
    
    Args:
        log_level: Logging level for file output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_file: Name of the log file
        console_level: Logging level for console output (defaults to log_level)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    console_numeric_level = getattr(
        logging,
        (console_level or log_level).upper(),
        numeric_level
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter()
    
    # Console handler - output to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - daily rotation
    file_handler = TimedRotatingFileHandler(
        filename=log_path / log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # Add date suffix to rotated files
    root_logger.addHandler(file_handler)
    
    # Log the logging configuration
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: file_level={log_level}, "
        f"console_level={console_level or log_level}, "
        f"log_file={log_path / log_file}"
    )


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Log an API request with structured information.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        client_ip: Client IP address
        user_agent: User agent string
    """
    logger = logging.getLogger("api.request")
    
    # Determine log level based on status code
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    # Build log message
    message = f"{method} {path} - {status_code} ({duration_ms:.2f}ms)"
    
    # Log with extra context
    logger.log(
        log_level,
        message,
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": user_agent
        }
    )


def log_error(
    error_type: str,
    message: str,
    details: Optional[dict] = None,
    exc_info: bool = False
) -> None:
    """
    Log an error with structured context.
    
    Args:
        error_type: Type/category of error
        message: Error message
        details: Additional error details
        exc_info: Whether to include exception traceback
    """
    logger = logging.getLogger("api.error")
    
    log_message = f"{error_type}: {message}"
    
    extra = {"error_type": error_type}
    if details:
        extra["details"] = details
    
    logger.error(log_message, extra=extra, exc_info=exc_info)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
