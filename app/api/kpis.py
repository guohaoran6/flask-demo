#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kpi interface implementation"""
from flask import g
from flask import request
from flask_restful import Resource, marshal_with
from jsonschema import ValidationError

from app import validators
from app.api import api
from app.customerrors import ForbiddenError, DataNotFoundError, UnsupportedFormatError
from app.extensions import db, auth
from app.models.experiment import Experiment, ExperimentModel
from app.models.variation import Variation
from app.models.condition import Condition
from app.models.kpi import Kpi
from app.api.experimentsV2 import ExperimentV2OutputJsonResource
from app.requestschema.kpi import kpi_create_request_schema, kpi_update_request_schema
from app.responseschema.kpi import kpi_collection_get_response, kpi_v2_get_response
from app.util import build_pagination_response, generate_reaction_query, generate_report_query, find_json_values_by_key
from app.loggers import CustomLogger

logger = CustomLogger(__name__)


class KpiCollectionFetchResource(Resource):
    """mapping to /v1/projects/<projectId>/kpis"""
    """ fetch kpi info for kpis mapped to a project """

    @auth.login_required
    @marshal_with(kpi_collection_get_response)
    def get(self, project_id):
        """fetch all kpis belonging to the project"""
        validators.check_id_format(project_id)
        validators.check_project_id_integrity(project_id)
        q = Kpi.query.filter(Kpi.project_id == project_id, Kpi.delete_flg == False)
        return build_pagination_response(request, q, project_id=project_id), 200


class KpiCollectionResource(Resource):
    """mapping to /v2/experiments/<experimentId>/kpis"""

    # making required dictionary fields as class variables for now, may have to move it in some setting/config file
    KEY = 'kpi_definitions'
    KPI_DEF = 'kpi_definition_name'
    MAIN = 'main_kpi'
    SETTINGS = 'kpi_settings'
    BASED_ON = 'based_on'
    EXPERIMENT_MODELS_FOR_KPI = ['MPB_MODEL', 'CMO_MODEL']


    @auth.login_required
    def post(self, experiment_id):
        validators.check_id_format(experiment_id)
        validators.check_experiment_id_integrity(experiment_id)
        req_json = request.get_json()
        validators.check_json(req_json, kpi_create_request_schema)
        experiment = Experiment.query.filter_by(experiment_id=experiment_id).one_or_none()
        kpi_name = experiment.project.name + '_' + experiment_id + '_' + 'kpi'
        # check one to one mapping
        kpi = Kpi.query.filter(Kpi.experiment_id == experiment_id).one_or_none()
        if not kpi:
            if not self._check_uniqueness(req_json[self.KEY]) or not self._check_main_kpi(req_json[self.KEY]):
                msg = "Wrong KPI Setting Format sent."
                logger.error(msg)
                raise ValidationError(msg)
            else:
                reaction_query = generate_reaction_query(experiment_id, req_json)
                report_query = generate_report_query(experiment_id, req_json)
                try:
                    new_kpi = Kpi(name=kpi_name,
                                  experiment_id=experiment_id,
                                  created_by=g.user.user_id,
                                  updated_by=g.user.user_id,
                                  reaction_query=reaction_query,
                                  report_query=report_query,
                                  kpi_settings=req_json,
                                  project_id=experiment.project_id)
                    # Set pattern_id in kpi_settings    
                    experimentModels = ExperimentModel.query.with_entities(ExperimentModel.model_name). \
                                            filter(ExperimentModel.experiment_id == experiment_id,
                                                       ExperimentModel.delete_flg == 0).all()
                    models = [model for (model,) in experimentModels]            
                    if any(model in models for model in self.EXPERIMENT_MODELS_FOR_KPI):                     
                        for kpi_definition in new_kpi.kpi_settings.get('kpi_definitions'):
                            if 'pattern_name' in kpi_definition:
                                pattern_name = find_json_values_by_key(kpi_definition, 'pattern_name')[0]
                                kpi_definition['pattern_id'] = self.retrieve_kpi_pattern_id(experiment_id, pattern_name)
                                
                    db.session.add(new_kpi)
                    db.session.commit()
                    experiment.kpi_id = new_kpi.kpi_id
                    db.session.commit()
                    # Prepare response
                    res = {
                        'kpiId': new_kpi.kpi_id
                    }
                    return res, 201                                     
                except Exception as e:
                    logger.error(str(e))
                    raise ValidationError("Unable to add new kpi due to : {}".format(str(e)))
        else:
            msg = "The kpi for experiment with experiment ID {} already exists".format(experiment_id)
            logger.error(msg)
            raise ForbiddenError(msg)

    @auth.login_required
    def put(self, experiment_id):
        validators.check_id_format(experiment_id)
        validators.check_experiment_id_integrity(experiment_id)
        experiment = Experiment.query.filter_by(experiment_id=experiment_id).one()
        validators.check_permission(project_id=experiment.project_id, user_id=g.user.user_id, module='kpi',
                                    function='edit')
        req_json = request.get_json()
        validators.check_json(req_json, kpi_update_request_schema)
        kpi = Kpi.query.filter(Kpi.experiment_id == experiment_id).one_or_none()
        if kpi:
            if not self._check_uniqueness(req_json[self.KEY]) or not self._check_main_kpi(req_json[self.KEY]):
                msg = "Wrong KPI Setting Format sent."
                logger.error(msg)
                raise ValidationError(msg)
            else:
                # Set pattern_id in kpi_settings    
                experimentModels = ExperimentModel.query.with_entities(ExperimentModel.model_name). \
                                    filter(ExperimentModel.experiment_id == experiment_id,
                                                       ExperimentModel.delete_flg == 0).all()
                models = [model for (model,) in experimentModels]     

                if any(model in models for model in self.EXPERIMENT_MODELS_FOR_KPI):
                    for kpi_definition in req_json.get('kpi_definitions'):
                        if 'pattern_name' in kpi_definition:
                            pattern_name = find_json_values_by_key(kpi_definition, 'pattern_name')[0]
                            kpi_definition['pattern_id'] = self.retrieve_kpi_pattern_id(experiment_id, pattern_name)

                kpi.kpi_settings = req_json
                kpi.updated_by = g.user.user_id
                kpi.reaction_query = generate_reaction_query(experiment_id, req_json)
                kpi.report_query = generate_report_query(experiment_id, req_json)
                kpi.if_custom_reaction_query = False
                kpi.if_custom_report_query = False
                db.session.commit()
                return {
                           'experimentId': kpi.experiment_id,
                           'kpiId': kpi.kpi_id
                       }, 200
        else:
            msg = "KPI for the experiment ID {} does not exist".format(experiment_id)
            logger.error(msg)
            raise DataNotFoundError(msg)

    @classmethod
    def _check_uniqueness(self, def_list):
        return not len(set([d[self.KPI_DEF] for d in def_list])) < len(def_list)

    @classmethod
    def _check_main_kpi(self, def_list):
        return ([d[self.MAIN] for d in def_list]).count(True) == 1

    @classmethod
    def retrieve_kpi_pattern_id(self, experiment_id, pattern_name):
        variations = Variation.query.filter(Variation.experiment_id == experiment_id).all()
        if variations:
            variation_ids = [variation.variation_id for variation in variations]
            condition = Condition.query.filter(Condition.name == str(pattern_name), Condition.variation_id.in_(variation_ids)).one_or_none()
            variation_type = None
            if condition:
                for variation in variations:
                    if variation.variation_id == condition.variation_id:
                        variation_type = variation.type_
            return ExperimentV2OutputJsonResource.format_pattern_id(variation_type, condition.variation_id, condition.condition_id)

    @marshal_with(kpi_v2_get_response)
    @auth.login_required
    def get(self, experiment_id):
        validators.check_id_format(experiment_id)
        validators.check_experiment_id_integrity(experiment_id)
        experiment = Experiment.query.filter_by(experiment_id=experiment_id).one()
        kpi = Kpi.query.filter(Kpi.kpi_id == experiment.kpi_id, Kpi.delete_flg == False). \
            with_entities(Kpi.kpi_id, Kpi.experiment_id, Kpi.reaction_query, Kpi.report_query,
                          Kpi.if_custom_reaction_query, Kpi.if_custom_report_query,
                          Kpi.kpi_settings, Kpi.kpi_id).one_or_none()
        if not kpi:
            msg = "No KPI is set for this experiment."
            logger.error(msg)
            return DataNotFoundError(msg)
        kpi = kpi._asdict()
        settings = kpi[self.SETTINGS]
        kpi[self.KEY], kpi[self.BASED_ON] = settings[self.KEY], settings[self.BASED_ON]
        return kpi

    @auth.login_required
    def delete(self, experiment_id):
        """ soft delete KPI, setting delete flag to True """
        validators.check_id_format(experiment_id)
        validators.check_experiment_id_integrity(experiment_id)
        kpi = Kpi.query.filter(Kpi.experiment_id == experiment_id).one_or_none()
        if kpi:
            kpi.delete_flg = True
            kpi.updated_by = g.user.user_id
            db.session.commit()
        return {
                   'kpiId': kpi.kpi_id
               }, 200


class KpiQueryCollectionResource(Resource):
    """ mapping to /v2/experiments/:experimentId/kpis/{type}_query """

    SUPPORTED_TYPES = ['report', 'reaction']

    @auth.login_required
    def put(self, experiment_id, type):
        validators.check_id_format(experiment_id)
        validators.check_experiment_id_integrity(experiment_id)
        experiment = Experiment.query.filter_by(experiment_id=experiment_id).one()
        validators.check_permission(project_id=experiment.project_id, user_id=g.user.user_id, module='kpi',
                                    function='editQuery')
        kpi = Kpi.query.filter(Kpi.experiment_id == experiment_id).one_or_none()
        if kpi:
            if type in self.SUPPORTED_TYPES:
                setattr(kpi, '{}_query'.format(type), request.data)
                setattr(kpi, 'if_custom_{}_query'.format(type), True)
                db.session.commit()
                return {
                    'if_{}Query_customized'.format(type): True
                }
            else:
                msg = "The format {} is not supported.".format(type)
                logger.error(msg)
                raise UnsupportedFormatError(msg)
        else:
            msg = "KPI for the experiment ID {} does not exist".format(experiment_id)
            logger.error(msg)
            raise DataNotFoundError(msg)

class KpiReactionQueryResource(Resource):
    """ mapping to /v2/experiments/:experimentId/reaction_query """

    @auth.login_required
    def post(self, experiment_id):
        kpi = Kpi.query.filter(Kpi.experiment_id == experiment_id).one_or_none()
        if kpi:
            setattr(kpi, 'reaction_query', generate_reaction_query(experiment_id, kpi.kpi_settings))
            db.session.commit()
        return None, 200

api.add_resource(KpiCollectionFetchResource, '/v1/projects/<project_id>/kpis')
api.add_resource(KpiCollectionResource, '/v2/experiments/<experiment_id>/kpis')
api.add_resource(KpiQueryCollectionResource, '/v2/experiments/<experiment_id>/kpis/<type>_query')
api.add_resource(KpiReactionQueryResource, '/v2/experiments/<experiment_id>/reaction_query')
