
"""Configure application logger
"""

import sys
import logging
import structlog
from pythonjsonlogger import jsonlogger

class Logging():
    """Create logging objects.
    """

    def __init__(self, config):
        """Initializes the Logging class
        """
        for log_conf in config.logging:
            self.configure_logging(log_conf,
                                   config.logging[log_conf]['log_level'],
                                   config.logging[log_conf]['log_mode'],
                                   config.logging[log_conf]['log_path'],
                                   config.logging[log_conf]['stdout'])

    def configure_logging(self, log_name, log_level, log_mode, log_path='', stdout=True):
        """Configure the application logger

        Args:
            log_name (str): name of the logger
            log_level (str): The level of logging for the application.
            log_mode (str): What kind of logging output to apply...
                text: Text logging is intended for users.
                json: Json logging is intended for parsing with a log aggregation system.
                standard: loggin with date and type for developers.
            log_path (str): path of the filename (if exist)
            stdout (bool): output on the console
        """

        if not log_level:
            log_level = logging.INFO

        if log_mode == 'json':
            log_formatter = jsonlogger.JsonFormatter()
        elif log_mode == 'text':
            log_formatter = logging.Formatter('%(message)s')
        elif log_mode == 'standard':
            log_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            log_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        root_logger = logging.getLogger(log_name)
        root_logger.setLevel(log_level)

        if log_path:
            fileHandler = logging.FileHandler(log_path, mode='w')
            fileHandler.setFormatter(log_formatter)
            root_logger.addHandler(fileHandler)
        if stdout:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(log_formatter)
            root_logger.addHandler(handler)

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.render_to_log_kwargs,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True
        )
