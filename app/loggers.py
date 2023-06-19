#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Custom Logger Framework for handling logs
"""

import logging
import os
import pytz
import sys

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from app.configs import CONFIG

LOG_FILENAME = CONFIG.LOG_FILE


class CustomFormatter(logging.Formatter):
    """customized logging formatter for support msec and UTC"""
    converter = datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created, tz=pytz.utc)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


class CustomLogger(object):
    loggers = set()
    log_formatter = ('[%(asctime)s][%(levelname)s][modulename: %(module)s, pathname:%(pathname)s,' 
        'funcname:%(funcName)s, lineno: %(lineno)d, loggername: %(name)s] -- : %(message)s')

    log_format = CustomFormatter(log_formatter, datefmt='%Y-%m-%dT%H:%M:%S.%fZ')

    def __init__(self, name):
        # Initial constructor
        self.name = name
        # Logger configuration.
        self.console_formatter = logging.Formatter(self.log_format)
        self.console_logger = logging.StreamHandler(sys.stdout)
        self.console_logger.setFormatter(self.console_formatter)
        # Complete logging config.
        self.logger = logging.getLogger(name)
        # avoiding multiple console prints of logs
        self.logger.propagate = False

        if name not in self.loggers:
            self.loggers.add(name)
            self.logger.addHandler(self.console_logger)

    def info(self, msg, extra=None):
        """
        overriding the inbuilt info method of logger to suit our use case
        can be configured with any logic, if required
        """
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=self.log_format)
        logging.info(msg, extra=extra)

    def error(self, msg, extra=None):
        """
        overriding the inbuilt error method of logger to suit our use case
        can be configured with any logic, if required
        """
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=self.log_format)
        logging.error(msg, extra=extra)

    def debug(self, msg, extra=None):
        """
        overriding the inbuilt debug method of logger to suit our use case
        can be configured with any logic, if required
        """
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=self.log_format)
        logging.debug(msg, extra=extra)

    def warning(self, msg, extra=None):
        """
        overriding the inbuilt warning method of logger to suit our use case
        can be configured with any logic, if required
        """
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=self.log_format)
        logging.warning(msg, extra=extra)

    def critical(self, msg, extra=None):
        """
        overriding the inbuilt critical method of logger to suit our use case
        can be configured with any logic, if required
        """
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=self.log_format)
        logging.critical(msg, extra=extra)


class GHPFileLogger(CustomLogger):

    def __init__(self):
        super(CustomLogger, self).__init__()

    def init_logger(self, app):
        # common custom_formatter
        custom_formatter = self.log_format
        # log level threshold to filter out the record which has lower level
        level_string = app.config['LOG_LEVEL'].upper()
        log_level = getattr(logging, level_string, None)  # i.e. logging.info, logging.debug, etc
        # set global logging config
        logging.basicConfig(level=log_level, disable_existing_loggers=False)
        # root logger and remove default console handler
        logger = logging.getLogger()
        logger.removeHandler(logger.handlers[0])
        # enable sqlalchemy raw SQL log
        logging.getLogger('sqlalchemy.engine').setLevel(app.config['SQLALCHEMY_ENGINE_LOG_LEVEL'])
        # show log on console
        if app.config['SHOW_LOG_ON_CONSOLE']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(custom_formatter)
            logger.addHandler(console_handler)
            logger.info("initialized console log output.")
        # save log into file
        if app.config['OUTPUT_LOG_TO_FILE']:
            # disable writing log into file if log file path not specified
            if not os.path.exists(os.path.dirname(LOG_FILENAME)):
                os.makedirs(os.path.dirname(LOG_FILENAME))
            if not (os.path.exists(LOG_FILENAME)) :
                with open(LOG_FILENAME, 'w') as f:
                    f.write("")
            file_handler = TimedRotatingFileHandler(LOG_FILENAME, when='D', backupCount=90, encoding='utf8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(custom_formatter)
            logger.addHandler(file_handler)
            logger.info("initialized file log output to {}.".format(LOG_FILENAME))



