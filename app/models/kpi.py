#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kpi database model"""

from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import JSON

from app.extensions import db


class Kpi(db.Model):
    __tablename__ = 'kpi'
    kpi_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=False)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.experiment_id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    solution_type = db.Column(db.String)
    detail = db.Column(db.String)
    created_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    create_time = db.Column(db.DateTime(), server_default=func.current_timestamp())
    updated_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    update_time = db.Column(db.DateTime(), server_default=func.current_timestamp())
    delete_flg = db.Column(db.Boolean, default=False)
    kpi_settings = db.Column(JSON, nullable=False)
    reaction_query = db.Column(db.Text)
    if_custom_reaction_query = db.Column(db.Boolean, default=False)
    report_query = db.Column(db.Text)
    if_custom_report_query = db.Column(db.Boolean, default=False)
    # relationship
    experiment = db.relationship('Experiment', foreign_keys=experiment_id, uselist=False)
    editor = db.relationship('User', foreign_keys=updated_by, uselist=False)
    project = db.relationship('Project', foreign_keys=project_id, uselist=False)

    def __init__(self, **kwargs):
        """
        Using Flask SQLAlchemy's base model class to initialize the fields of the model
        Stores all the arguments given, isn't really necessary to define a constructor
        """
        super(Kpi, self).__init__(**kwargs)

    def __repr__(self):
        return '<Kpi {}>'.format(self.kpi_id if self.kpi_id else self.name)
