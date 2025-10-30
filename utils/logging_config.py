
import logging
import os
import logging.config

class LoggingConfig:
    LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, 'execution.log')

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            },
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': LOG_FILE,
                'formatter': 'default',
                'level': 'INFO',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO',
            },
        },
        'root': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    }

    @staticmethod
    def setup_logging():
        logging.config.dictConfig(LoggingConfig.LOGGING_CONFIG)