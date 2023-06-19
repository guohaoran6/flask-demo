#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common meta data response model schema."""
import six
from flask_restful import fields, marshal

from app.util import datetime2str

pagination_link_meta_data = {
    'prev': fields.String,
    'next': fields.String,
    'first': fields.String,
    'last': fields.String,
}

pagination_meta_data = {
    "page": fields.Integer,
    "perPage": fields.Integer,
    "pages": fields.Integer,
    "total": fields.Integer,
    "links": fields.Nested(pagination_link_meta_data)
}


class NestedWithEmpty(fields.Nested):
    """
    Allows returning an empty dictionary if marshaled value is None
    """

    def __init__(self, nested, allow_empty=False, **kwargs):
        self.allow_empty = allow_empty
        super(NestedWithEmpty, self).__init__(nested, **kwargs)

    def output(self, key, obj):
        value = fields.get_value(key if self.attribute is None else self.attribute, obj)
        if value is None:
            if self.allow_null:
                return None
            elif self.allow_empty:
                return {}
        return marshal(value, self.nested)


class FieldsStringToUpperCase(fields.Raw):
    def format(self, value):
        """enum value should be upper case, in case they got stored as lower case in DB."""
        try:
            return six.text_type(value).upper()
        except ValueError as ve:
            raise fields.MarshallingException(ve)


class FieldsDictFromList(fields.List):
    """convert a objects list to a dict by given key which is an attribute name of the objects
        e.g. [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'x'}]
            ==> {1: {'id': 1, 'name': 'test'}, 2: {'id': 2, 'name': 'x'}}  , given key='id'
    """

    def __init__(self, cls_or_instance, key, **kwargs):
        super(FieldsDictFromList, self).__init__(cls_or_instance, **kwargs)
        self.key = key

    def format(self, value):
        return {v[self.key]: v for v in super(FieldsDictFromList, self).format(value)}


class FieldsISODateTime(fields.DateTime):
    """output datetime in ISO format"""

    def format(self, value):
        return datetime2str(value)
