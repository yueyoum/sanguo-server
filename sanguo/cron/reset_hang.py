from _base import Logger

from core.mongoscheme import MongoHangRemainedTime


def reset():
    MongoHangRemainedTime.objects.delete()
    logger = Logger('reset_hang.log')
    logger.write("MongoHangRemainedTime Clean Done")
    logger.close()


if __name__ == '__main__':
    reset()

