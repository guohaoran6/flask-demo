#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import logging
import ConfigParser
from fabric.api import *
from datetime import datetime
from logging import FileHandler


def set_env(deploy_env):
    # logger
    env.logger = logging.getLogger(__name__)
    env.logger.setLevel(logging.INFO)
    handler = FileHandler('deploy.log')
    formatter = logging.Formatter('[%(asctime)s] (%(levelname)s) %(message)s')
    handler.setFormatter(formatter)
    env.logger.addHandler(handler)

    # read config file
    env.cfg = ConfigParser.SafeConfigParser()
    env.cfg.read('./conf/deploy.conf')
    env.user = env.cfg.get(deploy_env, 'user')
    env.hosts = env.cfg.get(deploy_env, 'host').split(',')
    env.deploy_path = env.cfg.get(deploy_env, 'deploy_path')
    env.backup_path = env.cfg.get(deploy_env, 'backup_path')

    # set path
    env.now = datetime.today().strftime('%Y%m%d%H%M%S')
    env.backup_dir = os.path.join(env.backup_path, 'rpds_{}_{}'.format(deploy_env, env.now))
    env.cfg_file = './conf/config_{}.conf'.format(deploy_env)

    # log
    env.logger.info('###### deploy start ######')
    env.logger.info('### settings ###')
    env.logger.info('now: {}'.format(env.now))
    env.logger.info('deploy env: {}'.format(deploy_env))
    env.logger.info('user: {}'.format(env.user))
    env.logger.info('hosts: {}'.format(env.hosts))
    env.logger.info('deploy path: {}'.format(env.deploy_path))
    env.logger.info('backup path: {}'.format(env.backup_path))


@task()
def dev():
    set_env('dev')


@task()
def stg():
    set_env('stg')


@task()
def ins():
    set_env('ins')


@task()
def prod():
    set_env('prod')


@task()
def deploy():
    """ Release to target directory.
    """
    env.logger.info('### stop gunicorn ###')
    run('pkill gunicorn')
    env.logger.info('### backup ###')
    with cd(env.backup_path):
        env.logger.info('backup dir: {}'.format(env.backup_dir))
        run('cp -pr {} {}'.format(env.deploy_path, env.backup_dir))

    env.logger.info('### deploy ###')
    run('rm -rf {}'.format(env.deploy_path))
    run('mkdir {}'.format(env.deploy_path))
    with cd(env.deploy_path):
        put('*', env.deploy_path)
        env.logger.info('config file: {}'.format(env.cfg_file))
        run('cp -f {} {}'.format(env.cfg_file, './cf/config.conf'))
        # create link to latest backup for rollback
        run('ln -nfs {} .latest_backup'.format(env.backup_dir))
        env.logger.info('### stop gunicorn ###')
        with prefix('GHPPYTHON'):
            result = run('gunicorn -w 1 -b 0.0.0.0:5000 '
                         '--access-logfile /usr/local/bis/logs/ghp-restful-api/access.log '
                         '--log-file /usr/local/bis/logs/ghp-restful-api/errors.log '
                         '--name GHP manage:app &')
            if result.failed:
                env.logger.warn('GHP API start failed!')
                env.logger.warn(result)
                sys.exit(1)
            else:
                env.logger.info('GHP API start successful!')


@task()
def rollback():
    env.logger.info('### roll back ###')
    with cd(env.deploy_path):
        latest_backup = run('readlink -f .latest_backup')
        env.logger.info('latest backup: {}'.format(latest_backup))
        run('rm -rf *')
        run('cp -pr {}/* ./'.format(latest_backup, env.backup_dir))


@task()
def simple_deploy():
    """ Release to target directory without backup.
    """
    env.logger.info('### simple deploy (just put files, no cleanup, no backup) ###')
    with cd(env.deploy_path):
        put('*', env.deploy_path)
        env.logger.info('config file: {}'.format(env.cfg_file))
        run('cp -f {} {}'.format(env.cfg_file, './cf/config.conf'))


@task()
def test_unit():
    """ Run unit test. """
    env.logger.info('### unit test ###')
    with cd(env.deploy_path):
        result = run('py.test -x -v tests/', warn_only=True)
        if result.failed:
            env.logger.warn('unit test failed!')
            env.logger.warn(result)
            sys.exit(1)
        else:
            env.logger.info('unit test passed!')
