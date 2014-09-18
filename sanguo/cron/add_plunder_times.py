# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'


from _base import Logger
from core.mongoscheme import MongoCharacter
from core.plunder import Plunder


def main():
    logger = Logger('add_plunder_times.log')
    chars = MongoCharacter.objects.all()
    for char in chars:
        plunder = Plunder(char.id)
        plunder.change_current_plunder_times(change_value=1, allow_overflow=False)

    logger.write("add done")
    logger.close()

if __name__ == '__main__':
    main()
