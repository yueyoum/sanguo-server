# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/19/14'

"""
All api requests are POST to HTTPS api server
This Lib Only define a apicall method.
"""

import requests

class APIFailure(Exception):
    pass


class APIClient(object):
    def back(self, req):
        if not req.ok:
            raise APIFailure()
        return req.json()


class HTTPAPIClient(APIClient):
    def make_request(self, data, cmd):
        req = requests.post(cmd, data=data)
        return req

    def __call__(self, data, cmd):
        req = self.make_request(data, cmd)
        return self.back(req)


class HTTPSAPIClient(HTTPAPIClient):
    @classmethod
    def install_pem(cls, pem):
        cls.pem = pem

    def make_request(self, data, cmd):
        req = requests.post(cmd, data=data, verify=False, cert=HTTPSAPIClient.pem)
        return req
