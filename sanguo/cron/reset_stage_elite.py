from _base import Logger

from core.mongoscheme import MongoStage


def reset():
    logger = Logger('reset_stage_elite.log')
    logger.write("Reset Stage Elite Times Start")
    for ms in MongoStage.objects.all():
        for k in ms.elites.keys():
            ms.elites[k] = 0
        ms.save()

    logger.write("Done")
    logger.close()


if __name__ == '__main__':
    reset()

