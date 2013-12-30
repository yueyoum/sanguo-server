#!/usr/bin/env python

import os
import sys

command = sys.argv[1]

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
SANGUO_PATH = os.path.dirname(CURRENT_PATH)

os.chdir(SANGUO_PATH)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sanguo.settings'

from core.equip import generate_and_save_equip, delete_equip
from apps.character.models import Character
from apps.item.models import Equipment
from apps.item.cache import CacheEquipment
from core.mongoscheme import MongoChar


def add():
    tid, level, char_id = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    if not Character.objects.filter(id=char_id).exists():
        print "Character %d NOT exists" % char_id
        return

    e = generate_and_save_equip(tid, level, char_id)
    print "add done. {0}".format(e.id)


def delete():
    _id = int(sys.argv[2])
    delete_equip(_id)


def show():
    place = sys.argv[2]
    char_id = int(sys.argv[3])
    if place == 'db':
        equips = Equipment.objects.filter(char_id=char_id).values_list('id', flat=True)
    elif place == 'mongo':
        char = MongoChar.objects.only('equips').get(id=char_id)
        equips = char.equips
    elif place == 'cache':
        equips = []
        for e in CacheEquipment.objects.all():
            equips.append(e.id)

    print equips


if command == 'add':
    add()
elif command == 'delete':
    delete()
elif command == 'show':
    show()
else:
    print 'Unkown command'


