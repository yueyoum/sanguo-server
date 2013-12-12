from core.signals import login_signal

from core.notify import login_notify

def login(account_id, server_id, char_obj, **kwargs):
    if char_obj:
        login_notify('noti:{0}'.format(char_obj.id), char_obj)


login_signal.connect(
    login,
    dispatch_uid = 'core.callbacks.account.login'
)

        
