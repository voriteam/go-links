"""GCP-compatible structured logging for Gunicorn."""
import json
import logging
import sys
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
            import traceback
            log_entry['exception'] = ''.join(traceback.format_exception(*record.exc_info))
        return json.dumps(log_entry)


class GCPLogger(Logger):
    """Custom Gunicorn logger for GCP Cloud Logging."""
    
    def setup(self, cfg):
        super().setup(cfg)
        self._set_handler(self.error_log, cfg.errorlog, JSONFormatter())
        if self.access_log and not self.access_log.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.access_log.addHandler(handler)
            self.access_log.setLevel(logging.INFO)
    
    def access(self, resp, req, environ, request_time):
        if not (self.access_log and self.access_log.handlers):
            return
        latency = request_time.total_seconds() if hasattr(request_time, 'total_seconds') else float(request_time)
        self.access_log.info(json.dumps({
            'severity': 'INFO',
            'message': f'{environ.get("REMOTE_ADDR", "-")} - "{req.method} {req.path} {req.version}" {resp.status_code} {getattr(resp, "response_length", "-")}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'httpRequest': {
                'requestMethod': req.method, 'requestUrl': req.path, 'status': resp.status_code,
                'userAgent': environ.get('HTTP_USER_AGENT', ''), 'remoteIp': environ.get('REMOTE_ADDR', ''),
                'latency': f'{latency:.6f}s',
            }
        }))


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
