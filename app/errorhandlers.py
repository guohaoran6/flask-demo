#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Manage custom error handlers."""
import logging

import flask
from itsdangerous import SignatureExpired, BadSignature
from jsonschema import ValidationError

from app.api import api
from app.customerrors import MultipleValidationError, DataNotFoundError, AuthenticationFailedError, ForbiddenError

logger = logging.getLogger(__name__)


class ErrorResponse(object):
    """General error response json format class"""

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def serialize(self):
        return {
            'code': self.code,
            'message': self.message
        }


# unexpected_error_response = ErrorResponse(500, 'Unexpected error happened, please contact system admin.')


@api.errorhandler(ValidationError)
def json_validation_error_handler(error):
    response = flask.jsonify(ErrorResponse(400, error.message).serialize())
    response.status_code = 400
    return response


@api.errorhandler(MultipleValidationError)
def multiple_json_validation_error_handler(error):
    """
    The difference between MultipleValidationError and ValidationError is
    that JVE contains all errors in its 'messages' property.
    """
    response = flask.jsonify(ErrorResponse(400, '; '.join(error.messages)).serialize())
    response.status_code = 400
    return response


@api.errorhandler(SignatureExpired)
def auth_token_expiration_error_handler(error):
    response = flask.jsonify(
        ErrorResponse(401, 'Your auth token has expired by {0}.'.format(str(error.date_signed))).serialize())
    response.status_code = 401
    return response


@api.errorhandler(BadSignature)
def auth_token_invalid_error_handler(error):
    response = flask.jsonify(ErrorResponse(401, 'Your auth token is invalid.').serialize())
    response.status_code = 401
    return response


@api.errorhandler(DataNotFoundError)
def data_not_found_error_handler(error):
    response = flask.jsonify(ErrorResponse(404, error.message).serialize())
    response.status_code = 404
    return response


@api.errorhandler(AuthenticationFailedError)
def data_not_found_error_handler(error):
    response = flask.jsonify(ErrorResponse(401, error.message).serialize())
    response.status_code = 401
    return response


@api.errorhandler(ForbiddenError)
def data_not_found_error_handler(error):
    response = flask.jsonify(ErrorResponse(409, error.message).serialize())
    response.status_code = 409
    return response


@api.errorhandler(Exception)
def db_integrity_error_handler(error):
    """this error handler will catch all the exception which doesn't match any above, it's hyper, be careful."""
    status_code = 500
    msg = error.message
    if hasattr(error, 'code') and error.code:
        status_code = error.code
    if hasattr(error, 'description') and error.description:
        msg = error.description
    # for some build-in Flask error
    response = flask.jsonify(ErrorResponse(status_code, msg).serialize())
    response.status_code = status_code
    logger.error(error, exc_info=True)
    return response

