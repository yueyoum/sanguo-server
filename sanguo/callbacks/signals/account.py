from core.signals import login_signal

from core.notify import login_notify


def login(account_id, server_id, char_id, **kwargs):
    if char_id:
        login_notify(char_id)


login_signal.connect(
    login,
    dispatch_uid='core.callbacks.account.login'
)

        
