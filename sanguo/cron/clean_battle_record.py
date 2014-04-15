import os
import glob
import datetime

from _base import Logger

from django.conf import settings

DAYS_DIFF = 7

def clean():
    now = datetime.datetime.now()
    DAY = now - datetime.timedelta(days=DAYS_DIFF)

    BATTLE_RECORD_PATH = settings.BATTLE_RECORD_PATH
    os.chdir(BATTLE_RECORD_PATH)
    amount = 0
    files = glob.glob('*.bin')
    for f in files:
        t = os.path.getctime(f)
        create_date = datetime.datetime.fromtimestamp(t)
        if create_date < DAY:
            os.unlink(f)
            amount += 1

    logger = Logger('clean_battle_record.log')
    logger.write("Clean Battle Record Done. Amount: {0}".format(amount))
    logger.close()


if __name__ == '__main__':
    clean()



