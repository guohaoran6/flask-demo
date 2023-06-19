#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask app factory."""
import logging
import logging.config

from flask import Flask
from flask_cors import CORS

from app.configs import CONFIG
from app.extensions import db, cache
from loggers import GHPFileLogger


def create_app(config_object=None):
    """
    Flask app factory method
    :param config_object: application configuration to used
    :return: Flask app instance
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_object or CONFIG)

    # Logger init
    ghp_logger = GHPFileLogger()
    ghp_logger.init_logger(app)
    logger = logging.getLogger(__name__)
    logger.info("starting initializing...")

    # DB init
    db.init_app(app)

    # cache init
    cache.init_app(app, config=app.config)

    # API init
    from app.api import api_blueprint  # let logger init first
    app.register_blueprint(api_blueprint)
    logger.info("{0} started".format(app.name))

    # Allow CORS for same IP on a different port so you can run a demo API on the same
    # (See https://flask-cors.readthedocs.io/en/latest/ for how to set CORS)
    if app.config['DOCUMENTATION_HOSTING_ENABLED']:
        whitelist = app.config['DOCSERVER']
        CORS(app, resources={r"/api/*": {"origins": whitelist}})

    return app
