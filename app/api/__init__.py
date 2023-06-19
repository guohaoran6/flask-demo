#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from flask import Blueprint
from flask import current_app
from flask import make_response
from flask_restful import Api
from flask_restful_swagger import swagger

from app.configs import URL_PREFIX
from app.loggers import CustomLogger

logger = CustomLogger(__name__)


class ApiWithCustomErrorHandler(Api):
    """Patch Flask-style custom error handling feature into the Flask-RESTful api class.
    refer to https://gist.github.com/danijar/827bee07350a96bbf35b, https://github.com/flask-restful/flask-restful/pull/401
    """

    def __init__(self, *args, **kwargs):
        super(ApiWithCustomErrorHandler, self).__init__(*args, **kwargs)
        self._errorhandlers = []

    def errorhandler(self, exception_type):
        """
        Defined handlers for exceptions. Example:
        @api.errorhandler(ServerError):
        def handle_server_error(error):
            response = flask.jsonify({'message': error.message})
            response.status_code = error.status_code
            return response
        """

        def wrapper(func):
            self._errorhandlers.append((exception_type, func))
            # Sort error handlers to have sub exceptions first, so that those
            # take preference over base exceptions.
            self._errorhandlers = sorted(
                self._errorhandlers,
                key=lambda x: x[0],
                cmp=self._inheritance_comparator)
            # could not use logger as it's init later
            logger.info("binding error type with its handler ({0}, {1})".format(exception_type, func))
            return func

        return wrapper

    def handle_error(self, error, previous_errors=None):
        # Keep track of previous errors in the current chain of exception
        # handling in order to prevent infinite cycles that would occur if two
        # error handler raise the exception handled by the other.
        previous_errors = previous_errors or []
        previous_errors.append(type(error))
        # Try to find the first custom handler for the occurred exception.
        for exception_type, handler in self._errorhandlers:
            if not isinstance(error, exception_type):
                continue
            try:
                return handler(error)
            except Exception as new_error:
                if type(new_error) not in previous_errors:
                    return self.handle_error(new_error, previous_errors)
            break
        # If no matching handler was found or an infinite cycle is detected,
        # fall back to Flask-RESTful's error handling.
        return super(ApiWithCustomErrorHandler, self).handle_error(error)

    @staticmethod
    def _inheritance_comparator(lhs, rhs):
        lhs_sub = issubclass(lhs, rhs)
        rhs_sub = issubclass(lhs, rhs)
        if lhs_sub and not rhs_sub:
            return -1
        if rhs_sub and not lhs_sub:
            return 1
        return 0


api = ApiWithCustomErrorHandler(catch_all_404s=False)  # use customized Api() class to enable custom error handling
# add swagger auto-doc support, refer to https://github.com/rantav/flask-restful-swagger
# Also edit the index.html for swagger-ui/dist/index.html according to:
# * Validation disabled: https://github.com/z0mt3c/hapi-swaggered/issues/33
# * URL for JSON resource as: http://0.0.0.0:5000/api/spec/_/resource_list.json
api = swagger.docs(api, apiVersion='0.1', api_spec_url='/spec')
api_blueprint = Blueprint('api', __name__, url_prefix=URL_PREFIX)
api.init_app(api_blueprint)


# custom JSON serializer
@api.representation('application/json')
def output_json(data, code, headers=None):
    """Override the method in Flask-restful to enable Decimal encode support,
    makes a Flask response with a JSON encoded body"""
    settings = current_app.config.get('RESTFUL_JSON', {})

    # If we're in debug mode, and the indent is not set, we set it to a
    # reasonable value here.  Note that this won't override any existing value
    # that was set.  We also set the "sort_keys" value.
    # TODO this is moved into configs.py, can be removed I think
    if current_app.debug:
        settings.setdefault('indent', 4)
        settings.setdefault('sort_keys', True)

    import simplejson  # difference is only this line
    # always end the json dumps with a new line
    # see https://github.com/mitsuhiko/flask/pull/1262
    dumped = simplejson.dumps(data, **settings) + "\n"

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


def output_javascript(data, code, headers=None):
    """Expand Flask-restful to support output application/javascript MIME type response.
    The point where has to pay attention is the api.representation('xxx') relies on the header 'accepts' in request,
    response will not use this method if client doesn't put this MIME type in the 'accepts' header.
    """
    resp = make_response(data, code)
    resp.headers['Content-Type'] = 'application/javascript'
    resp.headers.extend(headers or {})
    return resp


# Import the resources to add the routes to the blueprint before the app is initialized
from . import users
from . import projects
from . import segments
from . import contents
from . import elements
from . import kpis
from . import experiments
from . import experimentsV2
from . import reports
from . import roles
from . import organizations
from . import role_managment
from . import service
from . import version

# Import custom error handler to the api instance which has init above
from app import errorhandlers
