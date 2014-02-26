from _base import Logger

from core.mongoscheme import MongoStoreCharLimit


def reset():
    MongoStoreCharLimit.objects.delete()
    logger = Logger('reset_store_player_limit.log')
    logger.write("MongoStoreCharLimit Clean Done")
    logger.close()


if __name__ == '__main__':
    reset()

