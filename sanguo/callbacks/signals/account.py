from core.signals import login_signal

from core.notify import login_notify
# from core.daily import OfficialDailyReward
from core.drives import redis_client
from core.arena import REDIS_DAY_KEY

def login(char_id, **kwargs):
    if char_id:
        # od = OfficialDailyReward(char_id)
        # od.check()
        if redis_client.zscore(REDIS_DAY_KEY, char_id) is None:
            redis_client.zadd(REDIS_DAY_KEY, char_id, 0)

        login_notify(char_id)


login_signal.connect(
    login,
    dispatch_uid='core.callbacks.account.login'
)
