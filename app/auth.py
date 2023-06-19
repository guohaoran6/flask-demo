#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Token generation and verification by lib itsdangerous (https://pythonhosted.org/itsdangerous)."""
from functools import wraps

import ldap
from flask import g
from itsdangerous import JSONWebSignatureSerializer as JWSSerializer, SignatureExpired, BadSignature

from app.configs import CONFIG
from app.customerrors import AuthenticationFailedError, DataNotFoundError
from app.models.user import User
from extensions import auth

from loggers import CustomLogger

logger = CustomLogger(__name__)
tokenizer = JWSSerializer(CONFIG.SECRET_KEY)


def generate_auth_token(payload):
    """generate auth token against given payload.
    :param payload: dict
    :return: string
    """

    return tokenizer.dumps(obj=payload, header_fields={'typ': 'JWT'})


@auth.verify_token
def verify_auth_token(token):
    """Decode the authentication token and get user_id from it"""
    if not CONFIG.ENABLE_AUTHENTICATION:
        # for unit test to pass the LDAP authentication
        if not hasattr(g, 'user'):
            g.user = User(account='test.user', email='test.user@dummy.com', system_admin=True)  # same as what in DB
            g.user.user_id = 9

        return True  # for unit test

    try:
        data = tokenizer.loads(token)
    except (SignatureExpired, BadSignature):
        raise AuthenticationFailedError("The token {} is invalid.".format(token))

    user = User.query.filter(User.user_id == data.get('user_id'), User.delete_flg == False).one_or_none()
    if user:
        g.user = user
    else:
        raise AuthenticationFailedError("The user {} does not exist.".format(data['user_id']))

    return True


def system_admin_restricted(func):
    """Decelerator for authenticate if the user try to get info which his/her role does not allow to do."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user:
            raise AuthenticationFailedError("You have to authenticate by your token first.")
        if not g.user.system_admin:
            raise AuthenticationFailedError("This function only allowed system administrator to use.")
        return func(*args, **kwargs)

    return wrapper


class LDAPClient(object):
    """LDAP Client
    Attention: UID here is a short account.
    If want use windows account/password authentication,
    see https://confluence.rakuten-it.com/confluence/display/acc2012/LDAP+Access#LDAPAccess-Related:ActiveDirectory"""

    def __init__(self, url, base_dn):
        self.url = url
        self.base_dn = base_dn
        self.client = ldap.initialize(url)
        self.client.protocol_version = ldap.VERSION3
        logger.debug("Initialized LDAP client, url=({0}), base_dn=({1})".format(url, base_dn))

    def _search(self, search_dn, search_cn):
        logger.debug("LDAP search {0}, for {1}".format(search_dn, search_cn))
        raw_list = self.client.search_s(search_dn, ldap.SCOPE_SUBTREE, search_cn, None)
        return raw_list

    def search_one_person(self, account):
        search_cn = '(&(cn={}))'.format(account)
        result = self._search(self.base_dn, search_cn)
        if result and len(result) == 1:
            for dn, entry in result:
                return dn, entry.get('uid')[0]
        elif len(result) < 1:
            raise DataNotFoundError("User {} not found.".format(account))
        else:
            raise AuthenticationFailedError("More than one user {} was found, could not authenticate.")

    def authenticate(self, dn, password):
        try:
            logger.debug("calling LDAP to authenticate for {}".format(dn))
            self.client.simple_bind_s(dn, password)
        except Exception as e:
            logger.warning(e.message)
            raise AuthenticationFailedError("LDAP authentication failed.")
        return True

    def authenticate_with_short_account(self, short_account, password):
        dn = 'uid={0},{1}'.format(short_account, self.base_dn)
        self.authenticate(dn, password)
