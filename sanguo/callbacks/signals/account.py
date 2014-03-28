from core.signals import login_signal

from core.notify import login_notify
from core.daily import OfficalDailyReward


def login(account_id, server_id, char_id, **kwargs):
    if char_id:
        od = OfficalDailyReward(char_id)
        od.check()
        login_notify(char_id)


login_signal.connect(
    login,
    dispatch_uid='core.callbacks.account.login'
)

