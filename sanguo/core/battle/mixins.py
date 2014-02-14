# -*- coding: utf-8 -*-



class StepHeroNotifyMixin(object):
    def fill_up_heor_notify(self, step_msg, target_id, hp, eff):
        # XXX 目前忽略掉exists
        for index, h in enumerate(step_msg.hero_notify):
            if h.target_id == target_id:
                step_msg.hero_notify[index].hp = hp
                new = step_msg.hero_notify[index].adds.add()
                new.id = eff.id
                new.value = eff.value
                return

        hero_noti = step_msg.hero_notify.add()
        hero_noti.target_id = target_id
        hero_noti.hp = hp
        new = hero_noti.adds.add()
        new.id = eff.id
        new.value = eff.value



class ActiveEffectMixin(object):
    def _using_eff_value(self, eff, target, attr_name, plus=True):
        base_value = getattr(target, attr_name)
        # 暴击按照固定值来处理
        if eff.id == 7 or eff.id == 8:
            value = eff.value
        else:
            value = base_value * eff.value / 100.0

        if plus:
            new_value = base_value + value
        else:
            new_value = base_value - value

        if new_value < 0:
            new_value = 0
        setattr(target, attr_name, new_value)


    def active_effect(self, target, eff, using_attr=True):
        if eff.id == 3:
            attr_name = 'using_attack' if using_attr else 'attack'
            plus = True
        elif eff.id == 4:
            attr_name = 'using_attack' if using_attr else 'attack'
            plus = False

        elif eff.id == 5:
            attr_name = 'using_defense' if using_attr else 'defense'
            plus = True
        elif eff.id == 6:
            attr_name = 'using_defense' if using_attr else 'defense'
            plus = False

        elif eff.id == 7:
            attr_name = 'using_crit' if using_attr else 'crit'
            plus = True
        elif eff.id == 8:
            attr_name = 'using_crit' if using_attr else 'crit'
            plus = False
        else:
            raise TypeError("using_effects, Unsupported eff: %d" % eff.id)

        self._using_eff_value(eff, target, attr_name, plus)
    