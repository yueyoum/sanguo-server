from django.dispatch import Signal

class SignalHeroWeGo(object):
    __slots__ = ['_signals']
    def __init__(self):
        self._signals = []

    def add(self, handler, **kwargs):
        self._signals.append((handler, kwargs))

    def emit(self):
        for handler, kwargs in self._signals:
            handler.send(**kwargs)



register_signal = Signal(providing_args=['account_id'])
login_signal = Signal(providing_args=['char_id'])

socket_changed_signal = Signal(providing_args=['socket_obj'])
socket_hero_changed_signal = Signal(providing_args=['char_id', 'socket_id', 'hero_id'])
pve_finished_signal = Signal(providing_args=['char_id', 'stage_id', 'win', 'star'])
plunder_finished_signal = Signal(providing_args=['from_char_id', 'to_char_id', 'from_win', 'standard_drop'])


char_level_up_signal = Signal(providing_args=['char_id', 'new_level'])
char_official_up_signal = Signal(providing_args=['char_id', 'new_official'])
char_gold_changed_signal = Signal(providing_args=['char_id', 'now_value', 'change_value'])
char_sycee_changed_signal = Signal(providing_args=['char_id', 'now_value', 'cost_value', 'add_value'])

hero_step_up_signal = Signal(providing_args=['char_id', 'hero_id', 'new_step'])
hero_changed_signal = Signal(providing_args=['hero_id'])
hero_add_signal = Signal(providing_args=['char_id', 'hero_ids', 'hero_original_ids', 'send_notify'])
hero_del_signal = Signal(providing_args=['char_id', 'hero_ids'])
hero_to_soul_signal = Signal(providing_args=['char_id', 'souls'])

equip_changed_signal = Signal(providing_args=['char_id', 'equip_obj'])

func_opened_signal = Signal(providing_args=['char_id', 'func_ids'])

new_purchase_signal = Signal(providing_args=['char_id', 'new_got', 'total_got'])
vip_changed_signal = Signal(providing_args=['char_id', 'old_vip', 'new_vip'])

new_friend_got_signal = Signal(providing_args=['char_id', 'new_friend_id', 'total_friends_amount'])

global_buff_changed_signal = Signal(providing_args=['char_id'])
