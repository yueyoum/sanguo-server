import os
import logging
from logging import handlers

from django.conf import settings

log = logging.getLogger('battle')
log.setLevel(logging.DEBUG)

fmt = logging.Formatter("%(levelname)s: %(message)s")

file_handle = handlers.TimedRotatingFileHandler(
    os.path.join(settings.TMP_PATH, 'battle.log'),
    when='D',
    backupCount=30
)

file_handle.setLevel(logging.DEBUG)
file_handle.setFormatter(fmt)

log.addHandler(file_handle)

if settings.DEBUG:
    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(fmt)
    log.addHandler(stream_handle)

from core.battle.battle import Battle
from core.battle.hero import BattleHero, BattleMonster

from core.formation import Formation

from apps.character.models import Character as ModelCharacter
from apps.stage.models import Stage as ModelStage


class PVE(Battle):
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
        monsters = ModelStage.all()[self.rival_id].decoded_monsters

        rival_heros = []
        for mid in monsters:
            if mid == 0:
                rival_heros.append(None)
            else:
                h = BattleMonster(mid)
                rival_heros.append(h)

        return rival_heros

    def get_my_name(self, my_id=None):
        if my_id is None:
            my_id = self.my_id
        cache_char = ModelCharacter.cache_obj(my_id)
        return cache_char.name


    def get_rival_name(self):
        return ModelStage.all()[self.rival_id].name



class PVP(PVE):
    def load_rival_heros(self):
        return self.load_my_heros(my_id=self.rival_id)

    def get_rival_name(self):
        return self.get_my_name(my_id=self.rival_id)



