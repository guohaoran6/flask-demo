#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Initializer for the Flask extensions.
reference:
    flask_httpauth - https://github.com/miguelgrinberg/Flask-HTTPAuth
    flask_sqlalchemy - https://github.com/mitsuhiko/flask-sqlalchemy
"""
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache

db = SQLAlchemy()
auth = HTTPTokenAuth()
cache = Cache()