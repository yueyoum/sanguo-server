# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-20'



class FightPowerMixin(object):
    @property
    def power(self):
        a = self.attack * 2.5 * (1 + self.crit / 200.0)
        # b = (self.hp + self.defense * 5) * (1 + self.dodge / 2.0)
        b = self.hp + self.defense * 5
        return int(a + b)


def level_up(current_level, current_exp, add_exp, up_needs_exp_func):
    new_exp = current_exp + add_exp
    while True:
        need_exp = up_needs_exp_func(current_level)
        if not need_exp:
            # 满级了
            new_exp = 0
            break

        if new_exp < need_exp:
            # 经验不够升级了
            break

        current_level += 1
        new_exp -= need_exp

    return current_level, new_exp
