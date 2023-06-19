#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kpi object response schema."""
from flask_restful import fields

from app.responseschema import pagination_meta_data, FieldsISODateTime
from app.responseschema.user import user_get_simple_response

kpi_get_response = {
    'kpiId': fields.Integer(attribute='kpi_id'),
    'name': fields.String,
    'description': fields.String,
    'solutionType': fields.String(attribute='solution_type'),
    'detail': fields.String,
    # 'createdBy': fields.Nested(user_get_simple_response, attribute='creator', allow_null=True),
    # 'createTime': fields.DateTime(attribute='create_time', dt_format='iso8601'),
    'updatedBy': fields.Nested(user_get_simple_response, attribute='editor', allow_null=True),
    'updateTime': FieldsISODateTime(attribute='update_time'),
    'version': fields.Integer(attribute='version'),
    'source': fields.Integer(attribute='source', default=None),
    'outdated': fields.Boolean(attribute='delete_flg')
}

kpi_collection_get_response = {
    'pagination': fields.Nested(pagination_meta_data),
    'records': fields.Nested(kpi_get_response)
}

kpi_v2_get_response = {
    "based_on": fields.String(default=None),
    "kpi_definitions": fields.List(fields.Raw(),default=None),
    "experimentId": fields.Integer(attribute='experiment_id'),
    "if_reactionQuery_customized": fields.Boolean(attribute='if_custom_reaction_query'),
    "if_reportQuery_customized": fields.Boolean(attribute='if_custom_report_query'),
    "kpiId": fields.Integer(attribute='kpi_id'),
    "reactionQuery": fields.String(attribute='reaction_query'),
    "reportQuery": fields.String(attribute='report_query')
}
