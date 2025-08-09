"""Logging configuration and utilities."""
import json
import logging
import logging.config
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "location": f"{record.pathname}:{record.lineno}",
            "function": record.funcName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_record.update(record.extra)
        
        return json.dumps(log_record, ensure_ascii=False)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health checks and metrics
        if request.url.path in {"/health", "/metrics", "/favicon.ico"}:
            return await call_next(request)
        
        # Log request
        logger = logging.getLogger("api.request")
        
        request_id = request.headers.get("X-Request-ID", "")
        client_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")
        
        extra = {
            "request_id": request_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }
        
        logger.info("Request received", extra=extra)
        
        # Process request
        start_time = datetime.now(timezone.utc)
        response = await self._process_request(request, call_next, extra)
        end_time = datetime.now(timezone.utc)
        
        # Log response
        process_time = (end_time - start_time).total_seconds() * 1000  # in milliseconds
        
        extra.update({
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2),
            "response_size": int(response.headers.get("content-length", 0)),
        })
        
        log_level = logging.ERROR if response.status_code >= 500 else logging.INFO
        logger.log(log_level, "Request completed", extra=extra)
        
        return response
    
    async def _process_request(self, request: Request, call_next, extra: Dict[str, Any]) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger = logging.getLogger("api.request")
            logger.exception(
                "Unhandled exception during request processing",
                extra=extra,
                exc_info=exc
            )
            raise

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    json_format: bool = True
) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, logs to stderr.
        json_format: Whether to use JSON format for logs.
    """
    # Configure logging format
    if json_format:
        formatter = {
            "()": f"{__name__}.JsonFormatter",
        }
    else:
        formatter = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S%z",
        }
    
    # Configure handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "json" if json_format else "default",
            "stream": sys.stderr,
        }
    }
    
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_file),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "level": log_level,
            "formatter": "json" if json_format else "default",
            "encoding": "utf8",
        }
    
    # Configure loggers
    loggers = {
        "": {  # root logger
            "handlers": list(handlers.keys()),
            "level": log_level,
            "propagate": False,
        },
        "api": {
            "handlers": list(handlers.keys()),
            "level": log_level,
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": list(handlers.keys()),
            "level": "WARNING",  # Set to INFO or DEBUG for SQL logging
            "propagate": False,
        },
        "uvicorn": {
            "handlers": list(handlers.keys()),
            "level": "WARNING",
            "propagate": False,
        },
    }
    
    # Apply configuration
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": formatter,
            "json": formatter,
        },
        "handlers": handlers,
        "loggers": loggers,
    })

# Create a logger instance for the application
logger = logging.getLogger("api")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name. If None, returns the root logger.
    """
    return logging.getLogger(name) if name else logging.getLogger()
