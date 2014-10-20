# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-10-20'


class Version(object):
    __slots__ = ['version',]
    def __init__(self, version):
        self.version = version

    def set_version(self, version):
        print "==== VERSION_CHANGE ===="
        print "==== old: {0} ====".format(self.version)
        self.version = version
        print "==== new: {0} ====".format(self.version)

version = Version("0.0.0.0")
