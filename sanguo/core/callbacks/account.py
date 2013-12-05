from core.signals import login_signal

from core import notify

def login(account_id, server_id, char_obj, **kwargs):
    if char_obj:
        notify.login_notify('noti:{0}'.format(char_obj.id), char_obj)


login_signal.connect(
    login,
    dispatch_uid = 'core.callbacks.account.login'
)

        
