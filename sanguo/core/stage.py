# -*- coding: utf-8 -*-


from mongoengine import DoesNotExist
from apps.stage.models import Stage as ModelStage
from core.mongoscheme import MongoStage

from utils import pack_msg
from core.msgpipe import publish_to_char
from core.world import Attachment

import protomsg

from core.exception import InvalidOperate
from core.battle import PVE


class Stage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.save()


    def battle(self, stage_id):
        all_stages = ModelStage.all()
        try:
            this_stage = all_stages[stage_id]
        except KeyError:
            raise InvalidOperate("PVE: Char {0} Try PVE in a NONE exist stage {1}".format(
                self.char_id, stage_id
            ))

        open_condition = this_stage.open_condition
        if open_condition and str(open_condition) not in self.stage.stages:
            raise InvalidOperate("PVE: Char {0} Try PVE in stage {1}. But Open Condition Check NOT passed. {2}".format(
                self.char_id, stage_id, open_condition
            ))

        battle_msg = protomsg.Battle()
        b = PVE(self.char_id, stage_id, battle_msg)
        b.start()

        star = False
        if battle_msg.first_ground.self_win and battle_msg.second_ground.self_win and battle_msg.third_ground.self_win:
            star = True

        if battle_msg.self_win:
            # 当前关卡通知
            msg = protomsg.CurrentStageNotify()
            self._msg_stage(msg.stage, stage_id, star)
            publish_to_char(self.char_id, pack_msg(msg))

            if str(stage_id) not in self.stage.stages:
                self.stage.stages[str(stage_id)] = star
            else:
                if not self.stage.stages[str(stage_id)]:
                    self.stage.stages[str(stage_id)] = star

            # 设置新关卡

            stage_new = this_stage.next
            if str(stage_new) not in self.stage.stages:
                if self.stage.stage_new != stage_new:
                    self.stage.stage_new = stage_new

                    self.send_new_stage_notify()
            self.stage.save()

        return battle_msg


    def get_drop(self, stage_id):
        """
        @param stage_id: stage id
        @type stage_id: int
        @return : exp, gold, stuffs. (0, 0, [(id, amount), (id, amount)])
        @rtype: (int, int, list)
        """
        # TODO
        return 0, 0, []

    def save_drop(self, stage_id):
        exp, gold, stuffs = self.get_drop(stage_id)

        attach = Attachment(self.char_id)
        attach.save_raw_attachment(exp=exp, gold=gold, stuffs=stuffs)

        return exp, gold, stuffs



    def _msg_stage(self, msg, stage_id, star):
        msg.id = stage_id
        msg.star = star

    def send_new_stage_notify(self):
        msg = protomsg.NewStageNotify()
        self._msg_stage(msg.stage, self.stage.stage_new, False)
        publish_to_char(self.char_id, pack_msg(msg))

    def send_already_stage_notify(self):
        msg = protomsg.AlreadyStageNotify()
        for _id, star in self.stage.stages.iteritems():
            s = msg.stages.add()
            self._msg_stage(s, int(_id), star)

        publish_to_char(self.char_id, pack_msg(msg))

