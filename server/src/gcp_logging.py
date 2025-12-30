"""GCP-compatible structured logging for Gunicorn."""
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from gunicorn.glogging import Logger


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for GCP."""
    SEVERITY_MAP = {
        logging.DEBUG: 'DEBUG', logging.INFO: 'INFO', logging.WARNING: 'WARNING',
        logging.ERROR: 'ERROR', logging.CRITICAL: 'CRITICAL',
    }
    
    def format(self, record):
        log_entry = {
            'severity': self.SEVERITY_MAP.get(record.levelno, 'INFO'),
            'message': record.getMessage(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        if record.exc_info:
            log_entry['exception'] = ''.join(traceback.format_exception(*record.exc_info))
        return json.dumps(log_entry)


class GCPLogger(Logger):
    """Custom Gunicorn logger for GCP Cloud Logging."""
    
    def setup(self, cfg):
        super().setup(cfg)
        self._set_handler(self.error_log, cfg.errorlog, JSONFormatter())


def configure_app_logging():
    """Configure Flask application logging for GCP."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    return root_logger