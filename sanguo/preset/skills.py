import json
from collections import defaultdict

from preset._base import data_path
from core.battle.skill import Skill, Effect

def load_data():
    with open(data_path('effect.json'), 'r') as f:
        content = json.loads(f.read())

    effects = defaultdict(lambda: [])
    for c in content:
        fields = c["fields"]
        skill_pk = fields.pop("skill")
        fields["type_id"] = fields.pop("effect_type")
        effects[skill_pk].append(Effect(**fields))

    with open(data_path('skill.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        sid = c["pk"]
        fields = c["fields"]
        fields.pop("name")
        fields.pop("des")

        fields["sid"] = sid
        fields["effects"] = effects[sid]

        data[sid] = Skill(**fields)
    return data

SKILLS = load_data()

