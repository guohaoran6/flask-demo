#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import re
import string
import time
import urllib
import xmlrpclib
from datetime import datetime, timedelta
from xml.dom.minidom import parseString

import paramiko
import pytz
from flask import url_for, request, render_template_string
from pytz.tzinfo import StaticTzInfo
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import or_
from unidecode import unidecode

from app.configs import CONFIG
from app.customerrors import DataNotFoundError, ForbiddenError
from app.loggers import CustomLogger
from app.requestschema.kpi import kpi_setting_schema

NA_PARAMS = ['', None]

logger = CustomLogger(__name__)


def is_integer(s):
    """Check if a string is an integer or not"""
    try:
        int(s)
    except ValueError:
        return False
    return True


class OffsetTime(StaticTzInfo):
    def __init__(self, offset):
        """A dumb timezone based on offset such as +05:30, -06:00, etc."""
        hours = int(offset[:3])
        minutes = int(offset[0] + offset[4:])
        self._utcoffset = timedelta(hours=hours, minutes=minutes)


def load_datetime(value, dt_fmt):
    """convert a ISO8601 format string of datetime to datetime object with timezone info if it has"""
    if dt_fmt.endswith('%z'):
        dt_fmt = dt_fmt[:-2]
        offset = value[-6:]
        value = value[:-6]

        if CONFIG.TIMEZONE_AWARENESS:
            return OffsetTime(offset).localize(datetime.strptime(value, dt_fmt))
        elif CONFIG.TIMEZONE_OFFSET != offset:
            # convert datetime to default timezone "+09:00"
            return pytz.timezone(CONFIG.TIMEZONE) \
                .normalize(OffsetTime(offset).localize(datetime.strptime(value, dt_fmt))).replace(tzinfo=None)
        else:
            return datetime.strptime(value, dt_fmt)
    return datetime.strptime(value, dt_fmt)


def str2datetime(s):
    """convert string to a datetime object"""
    return load_datetime(s, '%Y-%m-%dT%H:%M:%S%z')


def is_blank(s):
    """check if given string is None or an empty string"""
    return not (s and s.strip())


def datetime2str(dt):
    """convert string to a datetime object.
    timezone should be defined in config.
    """
    return pytz.timezone(CONFIG.TIMEZONE).localize(dt).replace(microsecond=0).isoformat()


# TODO reduce the limit per page after UI supported pagination
def build_pagination_response(request, query, max_per_page=200, **kwargs):
    """
    generate pagination supported response.

    :param request: Flask request instance
    :param query: Flask-sqlalchemy BaseQuery instance
    :param max_per_page: any integer
    :param kwargs: other S params to be used for generate paging URL
    :return:
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('perPage', max_per_page, type=int), max_per_page)
    # build-in pagination support, db_query should be BaseQuery object from flask-sqlalchemy
    r = query.paginate(page, per_page)
    # r => sql query result
    links = {}
    if r.has_prev:
        links['prev'] = url_for(request.endpoint, perPage=per_page, page=r.prev_num, **kwargs)
    if r.has_next:
        links['next'] = url_for(request.endpoint, perPage=per_page, page=r.next_num, **kwargs)
    links['first'] = url_for(request.endpoint, perPage=per_page, page=1, **kwargs)
    links['last'] = url_for(request.endpoint, perPage=per_page, page=r.pages, **kwargs)

    # response
    return {
        'pagination': {
            'page': page,
            'perPage': per_page,
            'pages': r.pages,
            'total': r.total,
            'links': links
        },
        'records': r.items
    }


def find_json_values_by_key(somejson, key):
    """fetch all values with the same key in a JSON."""

    def val(node):
        # Searches for the next Element Node containing Value
        e = node.nextSibling
        while e and e.nodeType != e.ELEMENT_NODE:
            e = e.nextSibling
        if e:
            if e.getElementsByTagName('string'):
                v = e.getElementsByTagName('string')[0].firstChild.nodeValue
            elif e.getElementsByTagName('int'):
                v = int(e.getElementsByTagName('int')[0].firstChild.nodeValue)
            else:
                v = None
            return v
        else:
            return None

    # parse the JSON as XML
    foo_dom = parseString(xmlrpclib.dumps((somejson,)))
    # and then search all the name tags which are P1's
    # and use the val user function to get the value
    return [val(node) for node in foo_dom.getElementsByTagName('name')
            if node.firstChild.nodeValue in key]


def build_experiment_searching_query(query, organization_id=None, project_id=None, search_word=None, start_after=None,
                                     start_before=None,
                                     end_after=None, end_before=None, overlap_period_start=None,
                                     overlap_period_end=None, device_type='PC', created_by=None, status=None,
                                     segment_type=None,
                                     sort='asc'):
    """utility method for sqlachemy """
    from app.models.experiment import Experiment
    from app.models.project import Project
    if organization_id:
        project_ids = Project.query.with_entities(Project.project_id).filter(
            Project.organisation_id == organization_id, Project.delete_flg == 0)
        project_ids = [id for (id,) in project_ids]
        query = query.filter(Experiment.project_id.in_(project_ids))
    if project_id:
        query = query.filter(Experiment.project_id == project_id)
    if search_word:
        query = query.filter(or_(Experiment.name.like(u'%{}%'.format(search_word)),
                                 Experiment.description.like(u'%{}%'.format(search_word))))
    if end_before:
        query = query.filter(Experiment.schedule_end_time < end_before)
    if end_after:
        query = query.filter(Experiment.schedule_end_time > end_after)
    if start_before:
        query = query.filter(Experiment.schedule_start_time < start_before)
    if start_after:
        query = query.filter(Experiment.schedule_start_time > start_after)
    if start_after and start_before:
        query = query.filter(and_(start_after < Experiment.schedule_start_time,
                                  start_before > Experiment.schedule_start_time))

    if overlap_period_start and overlap_period_end:
        query = query.filter(and_(overlap_period_start < Experiment.schedule_end_time,
                                  overlap_period_end > Experiment.schedule_start_time))
    if device_type:
        query = query.filter(Experiment.device_type == device_type)
    if segment_type:
        query = query.filter(Experiment.segment_type == segment_type)
    if status:
        query = query.filter(Experiment.status.in_(status))
    if created_by:
        query = query.filter(Experiment.created_by == created_by)
    if sort and 'asc' == sort.lower():
        query = query.order_by(asc('update_time'))
    else:
        query = query.order_by(desc('update_time'))
    return query


class RemoteHandler:
    def __init__(self, host, user):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=host, username=user, look_for_keys=True)

    def cmd(self, command, block=False):
        stdin, stdout, stderr = self.ssh.exec_command('bash -l -c "{}"'.format(command))
        if block:
            while not stdout.channel.exit_status_ready():
                continue
        error = stderr.readlines()
        # if have error
        if error:
            raise Exception('run command error: {} {} {}'.format(command, stdout.readlines(), error))
        return stdout.readlines()

    def scp(self, original, target):
        sftp = self.ssh.open_sftp()
        sftp.put(original, target)

    def close(self):
        if self.ssh:
            self.ssh.close()


def unescape_webcode(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&quot;", '"')
    s = s.replace("&apos;", "'")
    return s


def unescape_character(s):
    s = re.sub("\'[^]]*\'", lambda x: x.group(0).replace(';', '\;'),
               s)  # apparently this regex replaces ';' which was needed in the query, updated below
    s = s.replace("RCFILE\n\\;", "RCFILE\n;")  # ugly hack for correct semicolon replace after previous step
    s = re.sub("\'[^]]*\'", lambda x: x.group(0).replace('--', '\--'), s)
    return s


def generate_reaction_query(experiment_id, kpi_settings):
    """
    generates reaction hive query to be used by batch
    :param experiment_id:
    :param kpi_settings: kpi setting json
    :return:
    """
    from app.validators import check_json
    from app.models.experiment import Experiment

    check_json(kpi_settings, kpi_setting_schema)
    reaction_query = str()

    experiment = Experiment.query.filter(Experiment.experiment_id == experiment_id).one_or_none()
    if not experiment:
        raise DataNotFoundError("The experiment with given ID {} does not exist.".format(experiment_id))

    organization_settings = get_org_settings_by_experiment(experiment)

    # create a list of phxbanditpatterns
    variation_condition_combinations = list()
    for variation in experiment.variations:
        if not variation.is_root:
            continue
        variation_condition_combinations += get_all_variation_condition_combinations(variation)
    phxbanditpatterns = list()
    for combination in variation_condition_combinations:
        phxbanditpatterns.append('__'.join(combination))
    settings = True
    for kpi_definition in kpi_settings["kpi_definitions"]:

        if_r2d2 = False
        for kpi_condition in kpi_definition['kpi_conditions']:
            if kpi_condition["condition_type"] == "r2d2":
                if_r2d2 = True

        start_time = datetime.strftime(experiment.schedule_start_time, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strftime(experiment.schedule_end_time, "%Y-%m-%d %H:%M:%S")

        # r2d2 not allowed for Click Through Conversion or if there are other kpi conditions
        if if_r2d2 and (
                len(kpi_definition['kpi_conditions']) > 1 or kpi_definition['kpi_type'] == "clickThroughConversion"):
            raise ForbiddenError

        params = {
            "ghp_hive_dbname": CONFIG.HIVE_DB_NAME if organization_settings.template_type == 'REGULAR' else CONFIG.SEC_HIVE_DB_NAME,
            "reaction_table": CONFIG.HIVE_REACTION_TABLE,
            "kpi_name": kpi_definition['kpi_definition_name'],
            "kpi_conditions": kpi_definition['kpi_conditions'],
            "experiment_id": experiment_id,
            "phxbanditpatterns": phxbanditpatterns,
            "start_datetime": start_time,
            "end_datetime": end_time,
            "settings": settings
            }

        if len(kpi_definition['kpi_conditions']) == 1 and if_r2d2:
            reaction_query += render_template_string(organization_settings.reaction_r2d2_query_template, params=params)
        elif kpi_definition['kpi_type'] == "clickThroughConversion":
            kpi_conditions = []
            kpi_click_conditions = [condition for condition in kpi_definition['kpi_conditions'] if
                                    (not condition['condition_type'].startswith("conversion"))]
            # Getting clicks conditions if they exist
            if kpi_click_conditions:
                for i in range(len(kpi_click_conditions)):
                    kpi_conditions.append({"kpi": "click_" + str(i), "conditions": [kpi_click_conditions[i]]})

            # Getting conversion conditions and appending it at the end of the array
            # in order to left join conversion to the clicks at the end
            kpi_conversion_conditions = [condition for condition in kpi_definition['kpi_conditions'] if
                                         (condition['condition_type'].startswith("conversion"))]
            kpi_conditions.append({"kpi": "conversion", "conditions": kpi_conversion_conditions})

            params["kpi_conditions"] = kpi_conditions
            reaction_query += render_template_string(organization_settings.reaction_ctc_query_template, params=params)
        else:
            reaction_query += render_template_string(organization_settings.reaction_query_template, params=params)
        settings = False
    return unescape_character(unescape_webcode(unescape_webcode(reaction_query)))


def generate_report_query(experiment_id, kpi_settings):
    """
    generates report hive query to be used by batch
    :param experiment_id:
    :param kpi_setting: kpi setting json
    :return:
    """
    from app.validators import check_json
    from app.models.experiment import Experiment

    check_json(kpi_settings, kpi_setting_schema)

    # create a list of kpi_definition_names
    kpi_definition_names = list()
    for kpi_definition in kpi_settings["kpi_definitions"]:
        kpi_definition_names.append(kpi_definition['kpi_definition_name'])

    experiment = Experiment.query.filter(Experiment.experiment_id == experiment_id).one_or_none()
    if not experiment:
        raise DataNotFoundError("The experiment with given ID {} does not exist.".format(experiment_id))

    organization_settings = get_org_settings_by_experiment(experiment)

    # create a list of phxbanditpatterns
    variation_condition_combinations = list()
    for variation in experiment.variations:
        if not variation.is_root:
            continue
        variation_condition_combinations += get_all_variation_condition_combinations(variation)
    phxbanditpatterns = list()
    for combination in variation_condition_combinations:
        phxbanditpatterns.append('__'.join(combination))

    params = {
        "ghp_hive_dbname": CONFIG.HIVE_DB_NAME if organization_settings.template_type == 'REGULAR' else CONFIG.SEC_HIVE_DB_NAME,
        "report_table": CONFIG.HIVE_REPORT_TABLE,
        "kpi_names": kpi_definition_names,
        "experiment_id": experiment_id,
        "phxbanditpatterns": phxbanditpatterns,
        "kpi_count": len(kpi_settings["kpi_definitions"])
    }
    report_query = render_template_string(organization_settings.report_query_template, params=params)
    return unescape_character(unescape_webcode(unescape_webcode(report_query)))


def get_org_settings_by_experiment(experiment):
    """
    Return an organization settings model that the experiment is belong to
    :param experiment: experiment model
    :return: organisation_settings: organization settings model
    """
    if not experiment.project:
        raise DataNotFoundError("The project with given ID {} does not exist.".format(experiment.project_id))

    organisation = experiment.project.organisation

    if not organisation or not organisation.organisation_settings:
        raise DataNotFoundError(
            "The organization_settings with given ID {} does not exist.".format(experiment.project.organisation_id))

    return organisation.organisation_settings


def get_all_variation_condition_combinations(variation):
    """
    :param variation: experiment variation for which all the combinations are needed
    :return: (variation_type ,variation , condition) combinations of end-leaves
    """
    combinations = list()
    variation_type = variation.type_.lower()
    for condition in variation.conditions:
        # check if it's nested variation
        if condition.nested_variation:
            combinations += get_all_variation_condition_combinations(condition.nested_variation)  # recursive
            continue
        combinations.append((variation_type, str(variation.variation_id), str(condition.condition_id)))
    return combinations


def get_phxbanditpatterns(output_json, patterns=[]):
    """
    traverse through output_json and get all phxbanditpatterns
    :param output_json:
    :param patterns:
    :return:
    """
    for key in output_json:
        if key == 'nest':
            get_phxbanditpatterns(output_json[key])
        elif key == 'conditions':
            get_phxbanditpatterns(output_json[key])
        elif type(key) == dict:
            get_phxbanditpatterns(key)
        elif key == 'patternId':
            patterns.append(output_json[key])
    return patterns


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^:;~`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an ASCII-only output"""
    filtered_text = filter(lambda x: x in set(string.printable), text)
    result = []
    for word in _punct_re.split(filtered_text):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))


def cache_timeout(f):
    """
    decorator to implement dynamic cache timeout
    :param f:
    :return:
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        parser = args[0].req_parser.parse_args()
        f.cache_timeout = parser.get('timeout', CONFIG.CACHE_DEFAULT_TIMEOUT)
        return f(*args, **kwargs)

    return decorated_function


def cache_key():
    """
    add request arguments also to cache key , ** if not used cache key will only be path
    :return: key to be used for caching
    """
    args = request.args
    key = request.path + '?' + urllib.urlencode([(k, v) for k in sorted(args) for v in sorted(args.getlist(k))])
    return key


def timeit(method):
    """A decorator for measuring the execution time of a method"""

    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()
        logger.info("{} : {} executed {:4f} sec".format(
            args[0].__class__.__name__, method.__name__, te - ts
        ))
        return result

    return timed


def validate_datetime_with_timedelta(date, time_delta):
    """ A validator to validate datetime with time delta value """
    return str2datetime(date) >= datetime.now() + time_delta


def build_dag_name_str(experiment):
    return slugify('{}_{}_{}_{}_{}'.format(
        experiment.experiment_id,
        experiment.project.name,
        experiment.device_type,
        experiment.schedule_start_time.strftime('%Y%m%d%H%M%S'),
        experiment.version
    ))


def reformat_last_access_times(last_access_times):
    """reformat the last access times with day as the precision for searching purpose"""
    if len(last_access_times) == 1:
        from_time = last_access_times[0].replace(hour=0, minute=0, second=0)
        to_time = from_time + timedelta(days=1)
    else:
        from_time, to_time = last_access_times
        from_time = from_time.replace(hour=0, minute=0, second=0)
        to_time = to_time.replace(hour=0, minute=0, second=0) + timedelta(days=1)

    return from_time, to_time
