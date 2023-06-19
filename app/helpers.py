#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""helper classes"""

import base64
import re
import requests

from Crypto.Cipher import AES

from app.configs import CONFIG


def get_proxies():
    # Set empty proxy explicitly
    return {
        "http": "",
        "https": "",
    }


class CDNARequests(object):
    """Helper class for CDNA api request"""
    proxies = get_proxies()

    def post(self, path, json=None):
        json = json or {}
        response = requests.post(path, json=json, proxies=self.proxies)
        return response

    def get(self, path):
        response = requests.get(path, proxies=self.proxies)
        return response


class AesEbc(object):

    def __init__(self, key=None):
        self.cryptor = AES.new(key or CONFIG.AES_DEFAULT_KEY, AES.MODE_ECB)
        bs = AES.block_size
        self.pad = lambda s: s + (bs - len(s) % AES.block_size) * chr(bs - len(s) % bs)

    def encrypt(self, text):
        encrypted = self.cryptor.encrypt(self.pad(text))
        return base64.urlsafe_b64encode(encrypted)

    def decrypt(self, text):
        text += (len(text) % 4) * '='
        content = base64.urlsafe_b64decode(text)
        decrypted = self.cryptor.decrypt(content)
        try:
            return re.compile('[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f\n\r\t]').sub('', decrypted.decode())
        except Exception:
            raise ValueError("inputted value: {} can not be decrypted.".format(text))
