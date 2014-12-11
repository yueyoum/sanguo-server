# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-11'

from core.mongoscheme import MongoUnion

from core.union import send_notify
from core.union.base import UnionLoadBase, union_instance_check
from core.union.union import UnionDummy
from core.union.member import Member
from core.exception import SanguoException
from core.resource import Resource

from utils.functional import id_generator

from preset import errormsg
from preset.settings import UNION_NAME_MAX_LENGTH, UNION_CREATE_NEEDS_SYCEE, UNION_DEFAULT_DES


class UnionHelper(UnionLoadBase):
    @union_instance_check(UnionDummy, errormsg.UNION_CANNOT_CREATE_ALREADY_IN, "Union Create", "already in")
    def create(self, name):
        if len(name) > UNION_NAME_MAX_LENGTH:
            raise SanguoException(
                    errormsg.UNION_NAME_TOO_LONG,
                    self.char_id,
                    "Union Create",
                    "name too long: {0}".format(name.encode('utf-8'))
                    )


        if MongoUnion.objects.filter(name=name).count() > 0:
            raise SanguoException(
                    errormsg.UNION_NAME_ALREADY_EXIST,
                    self.char_id,
                    "Union Create",
                    "name already exist: {0}".format(name.encode('utf-8'))
                    )


        resource = Resource(self.char_id, "Union Create")

        with resource.check(sycee=-UNION_CREATE_NEEDS_SYCEE):
            new_id = id_generator('union')[0]
            mu = MongoUnion(id=new_id)
            mu.owner = self.char_id
            mu.name = name
            mu.bulletin = UNION_DEFAULT_DES
            mu.level = 1
            mu.contribute_points = 0
            mu.save()
            Member(self.char_id).join_union(new_id)

        send_notify(self.char_id)

