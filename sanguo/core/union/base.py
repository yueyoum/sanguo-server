# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

from core.exception import SanguoException
from core.union.union import Union

class UnionLoadBase(object):
    def __init__(self, char_id, union_id=None):
        self.char_id = char_id
        self.union = Union(char_id, union_id=union_id)



def union_instance_check(cls, err_msg, func_name, des=""):
    # err_msg: None | Msg. 如果是None表示检测失败后就返回None，否则raise异常
    def deco(func):
        def wrap(self, *args, **kwargs):
            if not isinstance(self.union, cls):
                if err_msg is None:
                    return None

                raise SanguoException(
                    err_msg,
                    self.char_id,
                    func_name,
                    des
                )

            return func(self, *args, **kwargs)
        return wrap
    return deco


