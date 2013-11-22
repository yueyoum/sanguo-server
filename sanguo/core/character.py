# -*- coding: utf-8 -*-

from core.drives import document_char, document_stage
from core import GLOBAL
from core.formation import save_socket, save_formation
from apps.character.models import CharHero

def char_initialize(char_id):
    # 随机三个武将，并上阵
    init_hero_ids = GLOBAL.HEROS.get_random_hero_ids(3)
    char_heros_list = [
            CharHero(char_id=char_id, hero_id=hid) for hid in init_hero_ids
            ]
    char_heros = CharHero.multi_create(char_heros_list)

    for index, h in enumerate(char_heros):
        save_socket(char_id, socket_id=index+1, hero=h.id)

    socket_ids = [
            1, 0, 0,
            2, 0, 0,
            3, 0, 0,
            ]

    save_formation(char_id, socket_ids)


    # 将关卡1设置为new 可进入
    document_stage.set(char_id, new=1)

def get_char_formation(char_id):
    char_formation = document_char.get(char_id, formation=1)
    return char_formation['formation']

