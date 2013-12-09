# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from itertools import groupby

from preset._base import data_path
from core.battle.skill import Skill, Effect

def load_data():
    # {
    #     sid: SkillObj,        
    # }

    # SkillObj:
    #     .id
    #     .mode
    #     .trig_prob
    #     .effects

    # effects:
    #     [(Effobj, Effobj), (Effobj, Effobj)]

    # 效果按组分好，并且将伤害效果放到最前面，同组效果一起命中/闪避

    with open(data_path('effect.json'), 'r') as f:
        content = json.loads(f.read())

    effects = defaultdict(lambda: [])
    for c in content:
        fields = c["fields"]
        skill_pk = fields.pop("skill")
        fields["type_id"] = fields.pop("effect_type")
        effects[skill_pk].append(Effect(**fields))

    for k, v in effects.iteritems():
        grouped_effs = []
        for _k, _g in groupby(v, lambda x: x.group_id):
            _g = list(_g)
            _g.sort(key=lambda x: x.type_id)
            if len(_g) >= 2 and _g[1].type_id == 2:
                _x = _g[1]
                _g.pop(1)
                _g.insert(0, _x)

            grouped_effs.append(_g)
        effects[k] = grouped_effs

    with open(data_path('skill.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        sid = c["pk"]
        fields = c["fields"]
        fields.pop("name")
        fields.pop("des")
        fields.pop("special_id")

        fields["sid"] = sid
        fields["effects"] = effects[sid]

        data[sid] = Skill(**fields)
    return data

SKILLS = load_data()


def load_combine_data():
    return {}

COMBINE_SKILLS = load_combine_data()

