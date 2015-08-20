import datetime

from core.signals import login_signal

from core.notify import login_notify
from core.mongoscheme import MongoCharacter
# from core.daily import OfficialDailyReward

def login(char_id, **kwargs):
    if char_id:
        # od = OfficialDailyReward(char_id)
        # od.check()

        now = datetime.datetime.utcnow()
        MongoCharacter._get_collection().update(
            {'_id': char_id},
            {'$set': {'last_login': now}}
        )

        login_notify(char_id)


login_signal.connect(
    login,
    dispatch_uid='core.callbacks.account.login'
)
