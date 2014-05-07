import os
import logging
from logging import handlers

from django.conf import settings

log = logging.getLogger('battle')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

fmt = logging.Formatter("%(levelname)s: %(message)s")

# file_handle = handlers.TimedRotatingFileHandler(
#     os.path.join(settings.TMP_PATH, 'battle.log'),
#     when='D',
#     backupCount=30
# )
#
# file_handle.setLevel(logging.DEBUG)
# file_handle.setFormatter(fmt)
#
# log.addHandler(file_handle)

if settings.ENABLE_BATTLE_LOG:
    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(fmt)
    log.addHandler(stream_handle)

from core.battle.battle import Battle
from core.battle.hero import BattleHero, BattleMonster

from core.formation import Formation
from core.character import Char


from preset.data import STAGES, STAGE_ELITE

class PVE(Battle):
    BATTLE_TYPE = 'PVE'
    def load_my_heros(self, my_id=None):
        if my_id is None:
            my_id = self.my_id

        f = Formation(my_id)

        my_heros = []
        for sid in f.formation.formation:
            if sid == 0:
                my_heros.append(None)
            else:
                socket = f.formation.sockets[str(sid)]
                hid = socket.hero
                if not hid:
                    my_heros.append(None)
                else:
                    my_heros.append(BattleHero(hid))

        return my_heros

    def load_rival_heros(self):
        stage = STAGES[self.rival_id]
        monsters = stage.decoded_monsters

        rival_heros = []
        for mid in monsters:
            if mid == 0:
                rival_heros.append(None)
            else:
                h = BattleMonster(mid, stage.level, stage.strength_modulus)
                rival_heros.append(h)

        return rival_heros

    def get_my_name(self, my_id=None):
        if my_id is None:
            my_id = self.my_id
        return Char(my_id).cacheobj.name


    def get_rival_name(self):
        return STAGES[self.rival_id].name




class ElitePVE(PVE):
    BATTLE_TYPE = 'ElitePVE'

    def load_rival_heros(self):
        stage = STAGE_ELITE[self.rival_id]
        monsters = stage.decoded_monsters

        rival_heros = []
        for mid in monsters:
            if mid == 0:
                rival_heros.append(None)
            else:
                h = BattleMonster(mid, stage.level, stage.strength_modulus)
                rival_heros.append(h)

        return rival_heros


    def get_rival_name(self):
        return STAGE_ELITE[self.rival_id].name



class PVP(PVE):
    BATTLE_TYPE = 'PVP'
    def load_rival_heros(self):
        return self.load_my_heros(my_id=self.rival_id)

    def get_rival_name(self):
        return self.get_my_name(my_id=self.rival_id)



