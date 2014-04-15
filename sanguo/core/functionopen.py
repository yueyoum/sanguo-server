# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'

from mongoengine import DoesNotExist

from mongoscheme import MongoFunctionOpen, MongoCharacter, MongoStage
from core.formation import Formation
from core.msgpipe import publish_to_char

from preset.data import FUNCTION_OPEN

from utils import pack_msg

from protomsg import FreezeFunctionNotify


FUNCTION_OPEN_FUNCS = {}
FUNCTION_OPEN_SOCKETS = {}
for k, v in FUNCTION_OPEN.items():
    if v.func_id:
        FUNCTION_OPEN_FUNCS[k] = v
    else:
        FUNCTION_OPEN_SOCKETS[k] = v

FUNCTION_OPEN_FUNCS_REV = {v.func_id: v for _, v in FUNCTION_OPEN_FUNCS.items()}



class FunctionOpen(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mf = MongoFunctionOpen.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mf = MongoFunctionOpen(id=self.char_id)
            self.mf.freeze.extend(FUNCTION_OPEN_FUNCS_REV.keys())
            self.mf.save()


    def trig(self, char_level, stage_id):
        opened_funcs = []
        for func_id in self.mf.freeze[:]:
            this_func = FUNCTION_OPEN_FUNCS_REV[func_id]
            if char_level >= this_func.char_level and stage_id >= this_func.stage_id:
                # OPEN
                self.mf.freeze.remove(func_id)
                opened_funcs.append(func_id)

        if opened_funcs:
            self.mf.save()

        f = Formation(self.char_id)
        for v in FUNCTION_OPEN_SOCKETS.values():
            if char_level >= v.char_level and stage_id >= v.stage_id:
                f.open_socket(v.socket_amount)
                if 20 not in opened_funcs:
                    opened_funcs.append(20)

        return opened_funcs


    def trig_by_char_level(self, char_level):
        s = MongoStage.objects.get(id=self.char_id)
        stage_ids = [int(i) for i in s.stages.keys()]
        stage_id = max(stage_ids)
        return self.trig(char_level, stage_id)


    def trig_by_stage_id(self, stage_id):
        c = MongoCharacter.objects.get(id=self.char_id)
        char_level = c.level
        return self.trig(char_level, stage_id)


    def send_notify(self):
        msg = FreezeFunctionNotify()
        msg.funcs.extend(self.mf.freeze)
        publish_to_char(self.char_id, pack_msg(msg))

