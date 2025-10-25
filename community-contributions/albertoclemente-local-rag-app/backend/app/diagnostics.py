"""
Diagnostics, logging, and resource monitoring utilities.
Provides correlation IDs, structured logging (JSONL), and system monitoring.
"""

import json
import logging
import logging.handlers
import os
import psutil
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.settings import get_settings


# Global correlation ID for request tracking
_correlation_id: Optional[str] = None


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: str):
    """Set the current correlation ID"""
    global _correlation_id
    _correlation_id = correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID"""
    return _correlation_id


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID"""
    old_id = get_correlation_id()
    try:
        set_correlation_id(correlation_id or generate_correlation_id())
        yield
    finally:
        set_correlation_id(old_id)


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        record.correlation_id = get_correlation_id() or "none"
        return True


class JSONLFormatter(logging.Formatter):
    """JSON Lines formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "none")
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "lineno", "funcName", "created",
                          "msecs", "relativeCreated", "thread", "threadName",
                          "processName", "process", "getMessage", "exc_info",
                          "exc_text", "stack_info", "correlation_id"]:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Setup structured logging with correlation IDs"""
    settings = get_settings()
    
    # Create logs directory
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(CorrelationFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (JSON Lines)
    log_file = logs_dir / "app.jsonl"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, 5 backups
    )
    file_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    file_handler.setFormatter(JSONLFormatter())
    file_handler.addFilter(CorrelationFilter())
    root_logger.addHandler(file_handler)
    
    # Disable some noisy loggers in production
    if not settings.debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


class ResourceMonitor:
    """System resource monitoring utility"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        memory_info = self.process.memory_info()
        return {
            "rss_bytes": memory_info.rss,
            "vms_bytes": memory_info.vms,
            "rss_mb": memory_info.rss / 1024 / 1024,
            "delta_mb": (memory_info.rss - self.start_memory) / 1024 / 1024
        }
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get overall system resource information"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "uptime_seconds": time.time() - self.start_time
        }
    
    def log_resources(self, logger: logging.Logger, level: int = logging.INFO):
        """Log current resource usage"""
        cpu = self.get_cpu_percent()
        memory = self.get_memory_usage()
        system = self.get_system_resources()
        
        logger.log(
            level,
            "Resource usage",
            extra={
                "cpu_percent": cpu,
                "memory_mb": memory["rss_mb"],
                "memory_delta_mb": memory["delta_mb"],
                "system_cpu_percent": system["cpu_percent"],
                "system_memory_percent": system["memory_percent"]
            }
        )


# Global resource monitor instance
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get the global resource monitor instance"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


def log_performance(func_name: str, duration: float, **kwargs):
    """Log performance metrics for a function"""
    logger = get_logger("performance")
    
    # Rename reserved LogRecord attributes to avoid conflicts
    safe_kwargs = {}
    for key, value in kwargs.items():
        if key in ('filename', 'lineno', 'funcName', 'module', 'pathname'):
            safe_kwargs[f'context_{key}'] = value
        else:
            safe_kwargs[key] = value
    
    logger.info(
        f"Function {func_name} completed",
        extra={
            "function": func_name,
            "duration_ms": duration * 1000,
            **safe_kwargs
        }
    )


@contextmanager
def performance_context(func_name: str, **kwargs):
    """Context manager for performance logging"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        log_performance(func_name, duration, **kwargs)
