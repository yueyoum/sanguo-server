from _base import Logger

from core.mongoscheme import MongoCounter


def reset():
    MongoCounter.objects.delete()
    logger = Logger('reset_counter.log')
    logger.write("MongoCounter Clean Done")
    logger.close()

if __name__ == '__main__':
    reset()

