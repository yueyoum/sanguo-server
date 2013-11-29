from django.dispatch import Signal

socket_changed_signal = Signal(providing_args=['hero', 'weapon', 'armor', 'jewelry'])
pve_finished_signal = Signal(providing_args=['stage_id', 'win', 'star'])
