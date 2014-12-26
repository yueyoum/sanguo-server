# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-26'

class Version(object):
    __slots__ = ['version',]
    def __init__(self, version):
        self.version = version

    def set_version(self, version):
        print "==== VERSION_CHANGE ===="
        print "==== old: {0} ====".format(self.version)
        self.version = version
        print "==== new: {0} ====".format(self.version)

    def _make_version_to_tuple(self, version):
        return tuple([int(i) for i in version.split('.')])

    def is_valid(self, version):
        self_version = self._make_version_to_tuple(self.version)
        target_version = self._make_version_to_tuple(version)
        return target_version >= self_version

    def is_little_than(self, version):
        self_version = self._make_version_to_tuple(self.version)
        target_version = self._make_version_to_tuple(version)

        self_major = self_version[:3]
        target_major = target_version[:3]
        return self_major < target_major

version = Version("0.0.0.0")

