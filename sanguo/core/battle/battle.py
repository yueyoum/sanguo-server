import logging

from core.battle.battle_field import BattleField

from protomsg import BattleHero as BattleHeroMsg

logger = logging.getLogger('battle')


class Ground(object):
    __slots__ = ['my_heros', 'rival_heros', 'msg', 'index']

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
                    msg_h.id = h.index
                    msg_h.hp = h.hp
                    msg_h.original_id = h.original_id
                    if h.HERO_TYPE == 1:
                        msg_h.ht = BattleHeroMsg.HERO
                    else:
                        msg_h.ht = BattleHeroMsg.MONSTER

        _fill_up_heros(self.my_heros, msg.self_heros)
        _fill_up_heros(self.rival_heros, msg.rival_heros)

        self.msg = msg


    def ground_power(self, heros):
        p = 0
        for h in heros:
            if h:
                p += h.power
        return p

    def team_hp(self, teams):
        hp = 0
        for h in teams:
            if h is None:
                continue
            hp += h.hp
        return hp

    def is_team_dead(self):
        if self.team_hp(self.my_heros) <= 0:
            return True, 1
        if self.team_hp(self.rival_heros) <= 0:
            return True, 2
        return False, None


    def start(self):
        #### LOG START
        logger.debug("#### Start Ground %d ####" % self.index)
        def _log_line(heros):
            line = []
            for h in heros:
                if h is None:
                    line.append("   .")
                else:
                    line.append("%4s" % str(h.id))

            line = ''.join(line)
            logger.debug(line)

        _log_line(self.rival_heros)
        _log_line(self.my_heros)
        ### LOG END


        # my_power = self.ground_power(self.my_heros)
        # rival_power = self.ground_power(self.rival_heros)
        #
        # if my_power >= rival_power:
        #     first_action_team = self.my_heros
        #     second_action_team = self.rival_heros
        # else:
        #     first_action_team = self.rival_heros
        #     second_action_team = self.my_heros
        first_action_team = self.my_heros
        second_action_team = self.rival_heros

        battle_field = BattleField(first_action_team, second_action_team, self.msg)
        for i in range(30):
            _dead, _team = self.is_team_dead()
            if _dead:
                self.msg.self_win = _team == 2
                break

            battle_field.action()

        if i == 29:
            self.msg.self_win = self.team_hp(self.my_heros) >= self.team_hp(self.rival_heros)

        logger.debug("Win = %s" % self.msg.self_win)
        return self.msg.self_win


class Battle(object):
    __slots__ = ['my_id', 'rival_id', 'my_heros', 'rival_heros', 'msg']
    BATTLE_TYPE = 'UNSET'

    def __init__(self, my_id, rival_id, msg):
        self.my_id = my_id
        self.rival_id = rival_id

        self.my_heros = self.load_my_heros()
        self.rival_heros = self.load_rival_heros()

        index = 0

        self_power = 0
        for h in self.my_heros:
            index += 1
            if h is not None:
                h.index = index
                self_power += h.power

        rival_power = 0
        for h in self.rival_heros:
            index += 1
            if h is not None:
                h.index = index
                rival_power += h.power

        msg.self_power = self_power
        msg.rival_power = rival_power
        msg.self_name = self.get_my_name()
        msg.rival_name = self.get_rival_name()
        self.msg = msg


    def load_my_heros(self, *args):
        raise NotImplementedError()

    def load_rival_heros(self, *args):
        raise NotImplementedError()

    def get_my_name(self, *args):
        raise NotImplementedError()

    def get_rival_name(self, *args):
        raise NotImplementedError()


    def start(self):
        logger.debug("###### Start Battle {0} : {1} VS {2} ######".format(self.BATTLE_TYPE, self.my_id, self.rival_id))
        heros_list = [str(h) for h in self.my_heros]
        logger.debug("My Heros:    %s" % str(heros_list))
        heros_list = [str(h) for h in self.rival_heros]
        logger.debug("Rival Heros: %s" % str(heros_list))

        grounds = []
        msgs = [self.msg.first_ground, self.msg.second_ground, self.msg.third_ground]
        index = 0
        for i in range(0, 9, 3):
            g = Ground(self.my_heros[i:i + 3], self.rival_heros[i:i + 3], msgs[index])
            g.index = index + 1
            grounds.append(g)
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

        logger.debug("Battle Win: %s" % self.msg.self_win)




