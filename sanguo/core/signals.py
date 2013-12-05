from django.dispatch import Signal

register_signal = Signal(providing_args=['account_id'])
login_signal = Signal(providing_args=['account_id', 'server_id', 'char_obj'])

socket_changed_signal = Signal(providing_args=['hero', 'weapon', 'armor', 'jewelry'])
pve_finished_signal = Signal(providing_args=['stage_id', 'win', 'star'])

hang_add_signal = Signal(providing_args=['char_id', 'stage_id', 'hours'])
hang_cancel_signal = Signal(providing_args=['char_id'])
hang_finished_signal = Signal(providing_args=['char_id'])

char_created_signal = Signal(providing_args=['account_id', 'server_id', 'char_obj'])
char_changed_signal = Signal(providing_args=['cache_char_obj'])

hero_changed_signal = Signal(providing_args=['cache_hero_obj'])
hero_add_signal = Signal(providing_args=['cache_hero_obj'])
hero_del_signal = Signal(providing_args=['hero_id'])

equip_changed_signal = Signal(providing_args=['cache_equip_obj'])
equip_add_signal = Signal(providing_args=['cache_equip_obj'])
equip_del_signal = Signal(providing_args=['equip_id'])

gem_changed_signal = Signal(providing_args=['gid', 'amount'])
gem_add_signal = Signal(providing_args=['gid', 'amount'])
gem_del_signal = Signal(providing_args=['gid'])
