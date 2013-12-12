
from core.signals import hang_finished_signal

def hang_job(char_id):
    hang_finished_signal.send(
        sender = None,
        char_id = char_id
    )
