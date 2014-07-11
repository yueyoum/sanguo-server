from django.dispatch import Signal

register_signal = Signal(providing_args=['account_id'])
login_signal = Signal(providing_args=['char_id'])

socket_changed_signal = Signal(providing_args=['socket_obj'])
socket_hero_changed_signal = Signal(providing_args=['char_id', 'socket_id', 'hero_id'])
pve_finished_signal = Signal(providing_args=['char_id', 'stage_id', 'win', 'star'])
plunder_finished_signal = Signal(providing_args=['from_char_id', 'to_char_id', 'is_crit'])


char_level_up_signal = Signal(providing_args=['char_id', 'new_level'])
char_official_up_signal = Signal(providing_args=['char_id', 'new_official'])
char_gold_changed_signal = Signal(providing_args=['char_id', 'now_value', 'change_value'])
char_sycee_changed_signal = Signal(providing_args=['char_id', 'now_value', 'change_value'])

hero_step_up_signal = Signal(providing_args=['char_id', 'hero_id', 'new_step'])
hero_changed_signal = Signal(providing_args=['hero_id'])
hero_add_signal = Signal(providing_args=['char_id', 'hero_ids', 'hero_original_ids', 'send_notify'])
hero_del_signal = Signal(providing_args=['char_id', 'hero_ids'])
hero_to_soul_signal = Signal(providing_args=['char_id', 'souls'])

equip_changed_signal = Signal(providing_args=['char_id', 'equip_obj'])

func_opened_signal = Signal(providing_args=['char_id', 'func_ids'])
