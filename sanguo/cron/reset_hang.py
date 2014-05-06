from _base import Logger

import traceback

from core.stage import Hang
from core.mongoscheme import MongoHang

def reset():
    logger = Logger('reset_hang.log')

    for mh in MongoHang.objects.all():
        h = Hang(mh.id)
        try:
            h.cronjob()
        except:
            e = traceback.format_exc()
            logger.write("==== Exception ====")
            logger.write(e)

    logger.write("Hang Reset Done")
    logger.close()


if __name__ == '__main__':
    reset()

