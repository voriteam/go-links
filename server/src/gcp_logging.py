"""
GCP-compatible structured logging for Gunicorn.

This module provides a custom Gunicorn logger that outputs JSON-formatted logs
with severity levels that Google Cloud Logging can properly parse.
"""
import json
import logging
import sys
from datetime import datetime, timezone

from gunicorn.glogging import Logger


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for GCP."""
    
    # Map Python logging levels to GCP severity levels
    SEVERITY_MAP = {
        logging.DEBUG: 'DEBUG',
        logging.INFO: 'INFO',
        logging.WARNING: 'WARNING',
        logging.ERROR: 'ERROR',
        logging.CRITICAL: 'CRITICAL',
    }
    
    def format(self, record):
        """Format log record as JSON."""
        severity = self.SEVERITY_MAP.get(record.levelno, 'INFO')
        
        log_entry = {
            'severity': severity,
            'message': record.getMessage(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # Add exception info if present
        if record.exc_info:
            import traceback
            log_entry['exception'] = ''.join(traceback.format_exception(*record.exc_info))
        
        return json.dumps(log_entry)


class GCPLogger(Logger):
    """
    Custom Gunicorn logger that outputs structured JSON logs compatible with GCP Cloud Logging.
    
    GCP Cloud Logging automatically parses JSON logs and extracts the 'severity' field
    to properly categorize logs in the Logs Explorer interface.
    """
    
    def setup(self, cfg):
        """Set up logging configuration."""
        super().setup(cfg)
        
        # Create custom JSON formatter
        json_formatter = JSONFormatter()
        
        # Configure the error logger (stderr) for structured output
        self._set_handler(
            self.error_log,
            cfg.errorlog,
            json_formatter
        )
        
        # Configure the access logger (stdout) for structured output  
        self._set_handler(
            self.access_log,
            cfg.accesslog,
            json_formatter
        )
    
    def access(self, resp, req, environ, request_time):
        """
        Log access with structured format.
        Override to output JSON format for access logs.
        """
        if not self.is_access_log_enabled():
            return
        
        # Convert timedelta to seconds (request_time is a timedelta object)
        latency_seconds = request_time.total_seconds() if hasattr(request_time, 'total_seconds') else float(request_time)
        
        # Build access log entry
        log_entry = {
            'severity': 'INFO',
            'message': f'{environ.get("REMOTE_ADDR", "-")} - "{req.method} {req.path} {req.version}" {resp.status_code} {getattr(resp, "response_length", "-")}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'httpRequest': {
                'requestMethod': req.method,
                'requestUrl': req.path,
                'status': resp.status_code,
                'userAgent': environ.get('HTTP_USER_AGENT', ''),
                'remoteIp': environ.get('REMOTE_ADDR', ''),
                'latency': f'{latency_seconds:.6f}s',
            }
        }
        
        self.access_log.info(json.dumps(log_entry))
    
    def is_access_log_enabled(self):
        """Check if access log is enabled."""
        return self.access_log and self.access_log.handlers


# Configure Python's root logger for Flask application logs
def configure_app_logging():
    """
    Configure Flask application logging to output GCP-compatible JSON logs.
    Call this from your Flask app initialization.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    return root_logger

