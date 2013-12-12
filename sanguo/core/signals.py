from django.dispatch import Signal

register_signal = Signal(providing_args=['account_id'])
login_signal = Signal(providing_args=['account_id', 'server_id', 'char_obj'])

socket_changed_signal = Signal(providing_args=['hero', 'weapon', 'armor', 'jewelry'])
pve_finished_signal = Signal(providing_args=['char_id', 'stage_id', 'win', 'star'])
plunder_finished_signal = Signal(providing_args=['from_char_id', 'to_char_id', 'is_npc', 'is_crit'])

prisoner_add_signal = Signal(providing_args=['char_id', 'mongo_prisoner_obj'])
prisoner_changed_signal = Signal(providing_args=['char_id', 'mongo_prisoner_obj'])
prisoner_del_signal = Signal(providing_args=['char_id', 'prisoner_id'])

hang_add_signal = Signal(providing_args=['char_id', 'hours'])
hang_cancel_signal = Signal(providing_args=['char_id'])
hang_finished_signal = Signal(providing_args=['char_id'])

char_created_signal = Signal(providing_args=['account_id', 'server_id', 'char_obj'])
char_changed_signal = Signal(providing_args=['char_obj'])

hero_changed_signal = Signal(providing_args=['cache_hero_obj'])
hero_add_signal = Signal(providing_args=['char_id', 'hero_ids'])
hero_del_signal = Signal(providing_args=['char_id', 'hero_ids'])

equip_changed_signal = Signal(providing_args=['cache_equip_obj'])
equip_add_signal = Signal(providing_args=['cache_equip_obj'])
equip_del_signal = Signal(providing_args=['char_id', 'equip_id'])

gem_changed_signal = Signal(providing_args=['char_id', 'gems'])
gem_add_signal = Signal(providing_args=['char_id', 'gems'])
gem_del_signal = Signal(providing_args=['char_id', 'gid'])


formation_changed_signal = Signal(providing_args=['char_id', 'socket_ids'])
