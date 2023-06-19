#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Validators unit module"""
from jsonschema import Draft4Validator, ValidationError
from datetime import datetime
from wtforms import validators

from app.customerrors import MultipleValidationError, DataNotFoundError, ForbiddenError
from app.models.content import Content
from app.models.element import Element
from app.models.experiment import Experiment
from app.models.kpi import Kpi
from app.models.project import Project
from app.models.segment import Segment, SegmentScv
from app.models.user import User
from app.models.role import Role
from app.models.organization import Organization, UserRoleOrganization
from app.models.service import Service
from app.models.segment_upload import SegmentUpload ,CDNASegmentUpload
from app.util import is_integer
from app.configs import Status, SUPPORTED_STATUS_TRANSFORMATIONS, SegmentStatus

from loggers import CustomLogger

logger = CustomLogger(__name__)


def check_json(json, schema):
    """JSON validator util by using JSON Schema lib (https://github.com/Julian/jsonschema)"""
    # check if json is empty
    if not json:
        msg = "JSON body may not be empty."
        logger.error(msg)
        raise ValidationError(msg)
    # validate by its schema
    validator = Draft4Validator(schema)
    e = None
    for error in sorted(validator.iter_errors(json), key=str):
        if not e:
            e = MultipleValidationError()
        e.messages.append(error.message)
    if e:
        logger.error(str(e))
        raise e


def check_id_format(*s):
    """Check if a string represents an integer."""
    for i in s:
        if not is_integer(i):
            msg = "{} is invalid format, ID is always an integer.".format(i)
            logger.error(msg)
            raise ValidationError(msg)


def check_project_id_integrity(project_id):
    """Check if projectId exists"""
    project = Project.query.filter(Project.project_id == project_id, Project.delete_flg == False).one_or_none()
    if not project:
        raise DataNotFoundError("The project with given ID {} does not exist.".format(project_id))


def check_experiment_id_integrity(experiment_id):
    """Check if experimentId exists"""
    experiment = Experiment.query.filter(Experiment.experiment_id == experiment_id,
                                         Experiment.delete_flg == False).one_or_none()
    if not experiment:
        msg = "The experiment with given ID {} does not exist.".format(experiment_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_kpi_id_integrity(kpi_id, project_id=None):
    """check if kpiId exists, and if it belongs to the project_id."""
    kpi = Kpi.query.filter(Kpi.kpi_id == kpi_id, Kpi.delete_flg == False).one_or_none()
    if not kpi:
        msg = "The kpi with given ID {} does not exist.".format(kpi_id)
        logger.error(msg)
        raise DataNotFoundError(msg)
    if project_id:
        if not kpi.project_id == project_id:
            msg = "The kpi(ID={}) does not belong to project(ID={}).".format(kpi_id, project_id)
            logger.error(msg)
            raise ValidationError(msg)


def check_user_id_integrity(user_id):
    """ check if userId exists """
    user = User.query.filter(User.user_id == user_id, User.delete_flg == False).one_or_none()
    if not user:
        msg = "The user with given ID {} does not exist.".format(user_id)
        logger.error(msg)
        raise DataNotFoundError(msg)
    return user


def check_role_id_integrity(role_id):
    """ check if the roleId exists """
    role = Role.query.filter(Role.role_id == role_id, Role.delete_flag == False).one_or_none()
    if not role:
        msg = "The role with given ID {} does not exist.".format(role_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_organization_id_integrity(organization_id):
    """ check if the organizationId exists """
    org = Organization.query.filter(Organization.organisation_id == organization_id,
                                    Organization.delete_flag == False).one_or_none()
    if not org:
        msg = "The organization with given ID {} does not exist.".format(organization_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_service_id_integrity(service_id):
    """ check if the organizationId exists """
    service = Service.query.filter(Service.service_id == service_id, Service.delete_flag == False).one_or_none()
    if not service:
        msg = "The service with given ID {} does not exist.".format(service_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_elements_have_same_type(element_types):
    """Currently experiment only aim to do one action at one time."""
    if len(element_types) > 1:
        msg = "Currently 1 experiment only accepts the elements with same action, i.e. REPLACE/REDIRECT."
        logger.error(msg)
        raise ValidationError(msg)


def check_element_id_integrity(element_ids, project_id=None):
    """check if elementId exists, and if it belongs to the project_id."""
    if isinstance(element_ids, int):
        # for v1, only has 1 element in top level or the json
        element = Element.query.filter(Element.element_id == element_ids).one_or_none()
        if not element:
            msg = "The element with given ID {} does not exist.".format(element_ids)
            logger.error(msg)
            raise DataNotFoundError(msg)
        if project_id:
            if not element.project_id == project_id:
                msg = "The element(ID={}) does not belong to project(ID={}).".format(element_ids, project_id)
                logger.error(msg)
                raise ValidationError(msg)
    elif isinstance(element_ids, set) or isinstance(element_ids, list) or isinstance(element_ids, tuple):
        element_ids = set([i for i in element_ids])
        # for v2, json may contain multiple element_id
        res = Element.query.with_entities(Element.element_id, Element.project_id, Element.action_type).filter(
            Element.element_id.in_(element_ids)).all()
        # check element type REPLACE/REDIRECT
        check_elements_have_same_type(set([i[2] for i in res]))
        element_ids_in_db = set([i[0] for i in res])
        element_id_diff = element_ids_in_db.symmetric_difference(element_ids)
        if element_id_diff:
            msg = "The element(ID={}) does not exist.".format(list(element_id_diff))
            logger.error(msg)
            raise DataNotFoundError(msg)
        if project_id:
            for i in res:
                wrong_ids = list()
                if i[1] != project_id:
                    wrong_ids.append(i[0])
                if wrong_ids:
                    msg = "The element(ID={}) does not belong to project(ID={}).".format(wrong_ids, project_id)
                    logger.error(msg)
                    raise ValidationError(msg)


def check_content_id_integrity(content_ids, project_id=None):
    """check if all content exists, and if they belong to the project."""
    if isinstance(content_ids, set):
        pass
    elif isinstance(content_ids, list):
        content_ids = set(content_ids)
    elif isinstance(content_ids, int):
        content_ids = {content_ids}
    elif isinstance(content_ids, tuple):
        content_ids = set([i for i in content_ids])
    else:
        msg = "check_content_id_integrity() does not accept the give parameter type: {}".format(type(content_ids))
        logger.error(msg)
        raise ValueError(msg)
    res = Content.query.with_entities(Content.content_id, Content.project_id).filter(
        Content.content_id.in_(content_ids)).all()
    content_ids_in_db = set([i[0] for i in res])
    content_id_diff = content_ids_in_db.symmetric_difference(content_ids)
    if content_id_diff:
        msg = "The content(ID={}) does not exist.".format(list(content_id_diff))
        logger.error(msg)
        raise DataNotFoundError(msg)
    if project_id:
        for i in res:
            wrong_ids = list()
            if i[1] != project_id:
                wrong_ids.append(i[0])
            if wrong_ids:
                msg = "The content(ID={}) does not belong to project(ID={}).".format(wrong_ids, project_id)
                logger.error(msg)
                raise ValidationError(msg)


def check_status_integrity(requested_status):
    """
    checks if given status is supported or not
    """
    if requested_status not in [status.value for status in Status]:
        msg = "{} status is not supported".format(requested_status)
        logger.error(msg)
        raise ValidationError(msg)


def check_status_transformation_integrity(current_status, requested_status):
    """
    checks is status transformation is valid or not
    :param current_status: current experiment status
    :param requested_status: requested change
    """
    if current_status == Status.ERROR.value:
        pass
    elif (current_status, requested_status) not in SUPPORTED_STATUS_TRANSFORMATIONS:
        msg = "Not a valid status transformation."
        logger.error(msg)
        raise ValidationError(msg)


def check_permission(user_id, module, function, organisation_id=None, project_id=None):
    """
    validate if user have permission to perform task related to api with module , funtion

    """
    user = User.query.filter(User.user_id == user_id, User.delete_flg == False).one()

    if not user.system_admin:

        if not organisation_id:
            check_project_id_integrity(project_id)
            project = Project.query.filter(Project.project_id == project_id).one()
            organisation_id = project.organisation_id

        check_organization_id_integrity(organisation_id)
        user_role_org = UserRoleOrganization.query.filter(UserRoleOrganization.user_id == user_id,
                                                          UserRoleOrganization.organisation_id == organisation_id,
                                                          UserRoleOrganization.delete_flag == 0).one_or_none()
        if not user_role_org:
            msg = "Logged in user don't have required permissions to perform this action. Contact your Organisation Admin."
            logger.error(msg)
            raise ForbiddenError(msg)
        role = Role.query.filter(Role.role_id == user_role_org.role_id, Role.delete_flag == False).one_or_none()
        if not role:
            msg = "Logged in user don't have required permissions to perform this action .Contact your Organisation Admin."
            logger.error(msg)
            raise ForbiddenError(msg)
        permissions = role.permissions
        try:
            if not permissions[module][function]:
                msg = "Logged in user don't have required permissions to perform this action .Contact your Organisation Admin."
                logger.error(msg)
                raise ForbiddenError(msg)
        except Exception as e:
            logger.warning(e.message)
            raise ForbiddenError(
                "Logged in user don't have required permissions to perform this action ."
                "Contact your Organisation Admin.")


def check_form(form):
    try:
        if not form.validate():
            msg = 'Form Validation Failed : {}'.format(form.errors)
            logger.error(msg)
            raise Exception(msg)
    except Exception as e:
        logger.error(e.message)
        raise ValidationError(e.message)


def check_segment_upload_id_integrity(organization_id, segment_upload_id):
    """ check if the segment_upload exists and belongs to given organisation """
    segment_upload = SegmentUpload.query.filter(SegmentUpload.organisation_id == organization_id,
                                                SegmentUpload.segment_upload_id == segment_upload_id,
                                                SegmentUpload.delete_flag == 0).one_or_none()
    if not segment_upload:
        msg = "The is no uploaded segment:{} for organisation:{}.".format(segment_upload_id, organization_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_segment_status_integrity(requested_status):
    """
    checks if given status is supported or not
    """
    if requested_status not in [status.value for status in SegmentStatus]:
        msg = "{} status is not supported".format(requested_status)
        logger.error(msg)
        raise ValidationError(msg)


def check_cdna_segment_upload_id_integrity(cdna_segment_upload_id):
    """ check if the segment_upload exists and belongs to given organisation """
    segment_upload = CDNASegmentUpload.query.filter(CDNASegmentUpload.cdna_segment_upload_id == cdna_segment_upload_id).one_or_none()
    if not segment_upload:
        msg = "There is no cdna segment with id {} .".format(cdna_segment_upload_id)
        logger.error(msg)
        raise DataNotFoundError(msg)


def check_days_to_clear_inactive_users(days):
    if not is_integer(days) or int(days) < 90:
        msg = "last access before days for clearing inactive user should be larger than 90 days, {}".format(days)
        logger.error(msg)
        raise ValidationError(msg)


def check_user_last_access_times(last_access_times):
    """check if use last access before days is larger than 0"""
    if not (1 <= len(last_access_times) <= 2):
        msg = "The size of last access time list should be 1 or 2, {}".format(len(last_access_times))
        logger.error(msg)
        raise ValidationError(msg)

    parsed_last_access_times = []
    for i in range(len(last_access_times)):
        try:
            # isoformat with microsecond=0
            parsed_last_access_times.append(datetime.strptime(last_access_times[i], '%Y-%m-%dT%H:%M:%S'))
        except ValueError:
            msg = "datetime format should be like 2021-01-01T12:00:00, {}".format(last_access_times[i])
            logger.error(msg)
            raise ValidationError(msg)

    if len(parsed_last_access_times) == 2 and parsed_last_access_times[0] > parsed_last_access_times[1]:
        msg = "last_access_times should be in ascending order, {}, {}".format(
            last_access_times[0], last_access_times[1])
        logger.error(msg)
        raise ValidationError(msg)

    return parsed_last_access_times
