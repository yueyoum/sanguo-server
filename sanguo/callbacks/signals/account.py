from core.signals import login_signal

from core.notify import login_notify
from core.daily import OfficalDailyReward

from worker import tasks

def login(account_id, server_id, char_id, **kwargs):
    # tasks.update_server_status.apply_async(args=[server_id], kwargs={'login_times': 1})
    if char_id:
        od = OfficalDailyReward(char_id)
        od.check()
        login_notify(char_id)


login_signal.connect(
    login,
    dispatch_uid='core.callbacks.account.login'
)

