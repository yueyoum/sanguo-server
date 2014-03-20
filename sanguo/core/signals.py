from django.dispatch import Signal

register_signal = Signal(providing_args=['account_id'])
login_signal = Signal(providing_args=['account_id', 'server_id', 'char_id'])

socket_changed_signal = Signal(providing_args=['socket_obj'])
pve_finished_signal = Signal(providing_args=['char_id', 'stage_id', 'win', 'star'])
plunder_finished_signal = Signal(providing_args=['from_char_id', 'to_char_id', 'is_crit'])


# hang_add_signal = Signal(providing_args=['char_id', 'hours'])
# hang_cancel_signal = Signal(providing_args=['char_id', 'actual_hours'])
hang_finished_signal = Signal(providing_args=['char_id', 'actual_seconds'])

char_created_signal = Signal(providing_args=['account_id', 'server_id', 'char_obj'])
char_updated_signal = Signal(providing_args=['char_id'])

hero_changed_signal = Signal(providing_args=['hero_id'])
hero_add_signal = Signal(providing_args=['char_id', 'hero_ids', 'hero_original_ids', 'send_notify'])
hero_del_signal = Signal(providing_args=['char_id', 'hero_ids'])

equip_changed_signal = Signal(providing_args=['char_id', 'equip_obj'])
