from django.http import HttpResponse


from core import GLOBAL
from core.battle.hero import BattleHero, MonsterHero
from core.battle.battle import Battle
from core.mongoscheme import MongoChar
from core.signals import pve_finished_signal
from core.stage import get_stage_drop

from utils import pack_msg

import protomsg


class PVE(Battle):
    def load_my_heros(self):
        char_data = MongoChar.objects.get(id=self.my_id)
        socket_ids = char_data.formation
        sockets = char_data.sockets

        self.my_heros = []
        for hid in socket_ids:
            if hid == 0:
                self.my_heros.append(None)
            else:
                sock = sockets[str(hid)]
                hid = sock.hero
                if not hid:
                    self.my_heros.append(None)
                else:
                    h = BattleHero(hid)
                    self.my_heros.append(h)



    def load_rival_heros(self):
        monster_ids = GLOBAL.STAGE[self.rival_id]['monsters']
        self.rival_heros = []
        for mid in monster_ids:
            if mid == 0:
                self.rival_heros.append(None)
            else:
                h = MonsterHero(mid)
                self.rival_heros.append(h)


def pve(request):
    msg = protomsg.Battle()

    req = request._proto
    print req

    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)

    b = PVE(char_id, req.stage_id, msg)
    b.start()
    
    star = False
    if msg.first_ground.self_win and msg.second_ground.self_win and msg.third_ground.self_win:
        star = True
    
    pve_finished_signal.send(
        sender = None,
        char_id = char_id,
        stage_id = req.stage_id,
        win = msg.self_win,
        star = star
    )
    
    drop_exp, drop_gold, drop_equips, drop_gems = get_stage_drop(char_id, req.stage_id)
    

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(msg)
    
    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    response.drop.equips.extend( [_id for _id, _l, _a in drop_equips] )
    response.drop.gems.extend( [_id for _id, _a in drop_gems] )

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


