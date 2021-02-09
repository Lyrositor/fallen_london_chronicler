from typing import Any, Dict

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "gunicorn": {"level": "INFO", "propagate": False, "handlers": ["console"]},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        }
    },
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s - %(message)s"
        },
    },
}
