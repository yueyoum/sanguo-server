from collections import defaultdict

from apps.character.models import CharHero
from core.battle.hero import BattleHero, MonsterHero
from core.formation import decode_formation
from core import GLOBAL
from core.battle.battle_field import BattleField
from core.character import get_char_formation

from protomsg import BattleHero as BattleHeroMsg


class Ground(object):
    def __init__(self, my_heros, rival_heros, msg):
        self.my_heros = my_heros
        self.rival_heros = rival_heros

        def _fill_up_heros(heros, msg_heros):
            for h in heros:
                msg_h = msg_heros.add()
                if h is None:
                    msg_h.id = 0
                    msg_h.original_id = 0
                    msg_h.hp = 0
                    msg_h.ht = BattleHeroMsg.HERO
                else:
                    msg_h.id = h.id
                    msg_h.hp = h.hp
                    msg_h.original_id = h.original_id
                    if h._hero_type == 1:
                        msg_h.ht = BattleHeroMsg.HERO
                    else:
                        msg_h.ht = BattleHeroMsg.MONSTER

        
        _fill_up_heros(self.my_heros, msg.self_heros)
        _fill_up_heros(self.rival_heros, msg.rival_heros)

        self.msg = msg
        self.find_combine_skills()


    def find_combine_skills(self):
        combine_skills = defaultdict(lambda: 0)
        for hero in self.my_heros:
            if hero is None:
                continue

            for s in hero.combine_skills:
                combine_skills[s] += 1

        avtive_combine_skills = []
        for s, count in combine_skills.iteritems():
            if count >= s.trig_condition:
                avtive_combine_skills.append(s)

    def cal_fighting_power(self, heros):
        return 100
    
    def my_team_hp(self):
        hp = 0
        for h in self.my_heros:
            if h is None:
                continue

            hp += h.hp
        return hp

    def rival_team_hp(self):
        hp = 0
        for h in self.rival_heros:
            if h is None:
                continue

            hp += h.hp
        return hp

    
    def is_team_dead(self):
        if self.my_team_hp() <= 0:
            return True, 1
        if self.rival_team_hp() <= 0:
            return True, 2

        return False, None


    def start(self):
        my_power = self.cal_fighting_power(self.my_heros)
        rival_power = self.cal_fighting_power(self.rival_heros)

        if my_power >= rival_power:
            first_action_team = self.my_heros
            second_action_team = self.rival_heros
        else:
            first_action_team = self.rival_heros
            second_action_team = self.my_heros


        battle_field = BattleField(first_action_team, second_action_team, self.msg)
        for i in range(30):
            _dead, _team = self.is_team_dead()
            if _dead:
                self.msg.self_win = _team == 2
                break

            battle_field.action()

        if i == 30:
            self.msg.self_win = self.my_team_hp() >= self.rival_team_hp()

        return self.msg.self_win



class Battle(object):
    def __init__(self, my_id, rival_id, msg):
        self.my_id = my_id
        self.reval_id = rival_id

        self.load_my_heros()
        self.load_rival_heros()

        index = 0

        self_power = 0
        for h in self.my_heros:
            index += 1
            if h is not None:
                h.id = index
                self_power += h.cal_fighting_power()

        rival_power = 0
        for h in self.rival_heros:
            index += 1
            if h is not None:
                h.id = index
                rival_power += h.cal_fighting_power()

        msg.self_power = self_power
        msg.rival_power = rival_power
        msg.self_name = "self_name"
        msg.rival_name = "rival_name"
        self.msg = msg


    def load_my_heros(self):
        formation = get_char_formation(self.my_id)
        msg = decode_formation(formation)

        formation_hero_ids = [i for i in msg.hero_ids if i > 0]
        my_hero_objs = CharHero.objects.defer('char').filter(
                id__in=formation_hero_ids
                )
        id_hero_dict = dict(zip(formation_hero_ids, my_hero_objs))

        self.my_heros = []
        for hid in msg.hero_ids:
            if hid == 0:
                self.my_heros.append(None)
            else:
                this_hero = id_hero_dict[hid]
                h = BattleHero(
                    this_hero.id,
                    this_hero.hero_id,
                    this_hero.exp
                    )
                h._hero_type = 1
                self.my_heros.append(
                        h
                        )


    def load_rival_heros(self):
        raise NotImplementedError()



    def start(self):
        grounds = []
        msgs = [self.msg.first_ground, self.msg.second_ground, self.msg.third_ground]
        index = 0
        for i in range(0, 9, 3):
            grounds.append(
                    Ground(self.my_heros[i:i+3], self.rival_heros[i:i+3], msgs[index])
                    )
            index += 1

        win_count = 0
        for g in grounds:
            win = g.start()
            if win:
                win_count += 1

        if win_count >= 2:
            self.msg.self_win = True
        else:
            self.msg.self_win = False





class PVE(Battle):
    def load_rival_heros(self):
        monster_ids = GLOBAL.STAGE[self.rival_id]['monsters']
        self.rival_heros = []
        for mid in monster_ids:
            if mid == 0:
                self.rival_heros.append(None)
            else:
                h = MonsterHero(mid)
                h._hero_type = 2
                self.rival_heros.append(h)


