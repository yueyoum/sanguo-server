class ActiveEffectMixin(object):
    def _cal_eff_value(self, eff, target, attr_name):
        base_value = getattr(target, attr_name)

        if eff.is_percent:
            return eff.value / 100.0 * base_value
        return eff.value

    def _using_eff_value(self, eff, target, attr_name, plus=True):
        base_value = getattr(target, attr_name)
        value = self._cal_eff_value(eff, target, attr_name)

        if plus:
            new_value = base_value + value
        else:
            new_value = base_value - value
            if new_value < 0:
                new_value = 0
        setattr(target, attr_name, new_value)


    def _active_effect(self, target, eff, using_attr=True):
        if eff.type_id == 3:
            attr_name = 'using_attack' if using_attr else 'attack'
            plus = True
        elif eff.type_id == 4:
            attr_name = 'using_attack' if using_attr else 'attack'
            plus = False

        elif eff.type_id == 5:
            attr_name = 'using_defense' if using_attr else 'defense'
            plus = True
        elif eff.type_id == 6:
            attr_name = 'using_defense' if using_attr else 'defense'
            plus = False

        elif eff.type_id == 7:
            attr_name = 'using_dodge' if using_attr else 'dodge'
            plus = True
        elif eff.type_id == 8:
            attr_name = 'using_dodge' if using_attr else 'dodge'
            plus = False

        elif eff.type_id == 9:
            attr_name = 'using_crit' if using_attr else 'crit'
            plus = True
        elif eff.type_id == 10:
            attr_name = 'using_crit' if using_attr else 'crit'
            plus = False

        elif eff.type_id == 14:
            if using_attr:
                raise Exception("using_effects, eff.type_id=14 and using_attr")
            attr_name = 'hp'
            plus = True
        else:
            raise TypeError("using_effects, Unsupported eff: %d" % eff.type_id)

        self._using_eff_value(eff, target, attr_name, plus)
    