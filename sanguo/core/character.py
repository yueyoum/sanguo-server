# -*- coding: utf-8 -*-

from core.drives import document_char, document_stage
from core import GLOBAL
from core.formation import encode_formation_with_raw_data
from apps.character.models import CharHero

def char_initialize(char_id):
    # 随机三个武将，并上阵
    init_hero_ids = GLOBAL.HEROS.get_random_hero_ids(3)
    char_heros_list = [
            CharHero(char_id=char_id, hero_id=hid) for hid in init_hero_ids
            ]
    char_heros = CharHero.multi_create(char_heros_list)

    encoded_formation = encode_formation_with_raw_data(
            9,
            [
                char_heros[0].id, 0, 0,
                char_heros[1].id, 0, 0,
                char_heros[2].id, 0, 0,
            ]
            )
    document_char.set(char_id, formation=encoded_formation)

    # 将关卡1设置为new 可进入
    document_stage.set(char_id, new=1)

    return char_heros, encoded_formation



def get_char_formation(char_id):
    char_formation = document_char.get(char_id, formation=1)
    return char_formation['formation']

