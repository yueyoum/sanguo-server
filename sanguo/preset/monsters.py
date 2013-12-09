import json
from preset._base import data_path

def load_data():
    with open(data_path('monster.json'), 'r') as f:
        content = json.loads(f.read())

    def _parse_skills(text):
        if not text:
            return []
        skills = [int(s) for s in text.split(',')]
        if len(skills) == 1 and skills[0] == 0:
            return []
        return skills


    data = {}
    for c in content:
        field = c["fields"]
        field.pop("name")
        field.pop("avatar")
        field.pop("image")

        field["skills"] = _parse_skills(field['skills'])
        data[c["pk"]] = field

    return data

MONSTERS = load_data()

