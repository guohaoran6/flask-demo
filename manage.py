#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command line interface (CLI) for this program. Also it's the entrance."""
# following 3 lines are disable some noising warning messages in log
import warnings
from flask.exthook import ExtDeprecationWarning
from flask import url_for
from flask_script import Manager, Shell

from app import models
from app import create_app
from app.configs import CONFIG
from app.extensions import db

warnings.simplefilter('ignore', ExtDeprecationWarning)


# Flask app init
app = create_app(CONFIG)  # config should be loaded dynamically

# CLI support init
manager = Manager(app)


@manager.command
def routes():
    """List all available url routing rules"""
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:40s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print line


def _make_context():
    return dict(app=app, db=db, models=models)


manager.add_command("shell", Shell(make_context=_make_context))


if __name__ == '__main__':
    manager.run()
