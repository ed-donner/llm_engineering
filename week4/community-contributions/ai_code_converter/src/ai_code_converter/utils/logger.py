"""Logging configuration for the CodeXchange AI."""

import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        if hasattr(record, 'duration'):
            log_data['duration'] = f"{record.duration:.4f}s"
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def log_execution_time(logger: logging.Logger) -> Callable:
    """Decorator to log function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log function entry
            logger.debug(
                "Function Entry | %s | Args: %s | Kwargs: %s",
                func.__name__,
                [str(arg) for arg in args],
                {k: str(v) for k, v in kwargs.items() if not any(sensitive in k.lower() for sensitive in ('password', 'key', 'token', 'secret'))}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log function exit
                logger.debug(
                    "Function Exit | %s | Duration: %.4fs",
                    func.__name__,
                    duration
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Function Error | %s | Duration: %.4fs | Error: %s",
                    func.__name__,
                    duration,
                    str(e),
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with both file and console output."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] [PID:%(process)d-%(threadName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    json_formatter = JSONFormatter()
    
    # Console handler with color coding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # File handler with daily rotation and JSON formatting
    log_file = log_dir / f"ai_converter_{datetime.now().strftime('%Y-%m-%d')}.json"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=30,  # Keep 30 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log initialization
    logger.info("="*50)
    logger.info("Logger Initialized")
    logger.info(f"Logger Name: {name}")
    logger.info(f"Log File: {log_file}")
    logger.info(f"Process ID: {os.getpid()}")
    logger.info(f"Thread ID: {threading.get_ident()}")
    logger.info(f"Thread Name: {threading.current_thread().name}")
    logger.info("="*50)
    
    return logger 