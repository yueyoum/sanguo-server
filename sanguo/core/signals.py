from django.dispatch import Signal

socket_changed_signal = Signal(providing_args=['hero', 'weapon', 'armor', 'jewelry'])
