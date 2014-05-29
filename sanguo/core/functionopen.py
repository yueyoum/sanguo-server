# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'

from mongoengine import DoesNotExist

from mongoscheme import MongoFunctionOpen, MongoCharacter, MongoStage
from core.formation import Formation
from core.msgpipe import publish_to_char

from preset.data import FUNCTION_DEFINE
from utils import pack_msg
from protomsg import FreezeFunctionNotify

FUNC_SOCKET_AMOUNT_TABLE = {
    50: 5,
    51: 6,
    52: 7,
    53: 8,
}


class FunctionOpen(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mf = MongoFunctionOpen.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mf = MongoFunctionOpen(id=self.char_id)
            self.mf.freeze.extend(FUNCTION_DEFINE.keys())
            self.mf.save()

    def _open(self, fun_id):
        self.mf.freeze.remove(fun_id)
        self.mf.save()
        self.send_notify()


    def trig(self, char_level, stage_id=None):
        try:
            s = MongoStage.objects.get(id=self.char_id)
            passed_stages = s.stages.keys()
        except DoesNotExist:
            passed_stages = []

        passed_stages.append('0')
        if stage_id:
            passed_stages.append(str(stage_id))

        opened_funcs = []
        for func_id in self.mf.freeze[:]:
            this_func = FUNCTION_DEFINE[func_id]
            if char_level >= this_func.char_level and str(this_func.stage_id) in passed_stages:
                # OPEN
                self.mf.freeze.remove(func_id)
                opened_funcs.append(func_id)

        if opened_funcs:
            self.mf.save()

        f = Formation(self.char_id)
        for of in opened_funcs[:]:
            if of in FUNC_SOCKET_AMOUNT_TABLE:
                opened = f.open_socket(FUNC_SOCKET_AMOUNT_TABLE[of])
                if not opened:
                    opened_funcs.remove(of)

        return opened_funcs


    def trig_by_char_level(self, char_level):
        return self.trig(char_level)


    def trig_by_stage_id(self, stage_id):
        c = MongoCharacter.objects.get(id=self.char_id)
        char_level = c.level
        return self.trig(char_level, stage_id)


    def send_notify(self):
        msg = FreezeFunctionNotify()
        msg.funcs.extend(self.mf.freeze)
        publish_to_char(self.char_id, pack_msg(msg))

