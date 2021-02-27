import logging.config

from fallen_london_chronicler.config import config as _config
from fallen_london_chronicler.log import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)

bind = f"0.0.0.0:{_config.app_port}"
reload = _config.debug
worker_class = "uvicorn.workers.UvicornWorker"
workers = 4

logconfig_dict = LOGGING_CONFIG
