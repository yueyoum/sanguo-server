import json
from preset._base import data_path

def load_data():
    with open(data_path('monster.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        field = c["fields"]
        field.pop("name")
        field.pop("avatar")
        field.pop("image")
        field["skills"] = field["skills"].split(',')

        data[c["pk"]] = field

    return data

MONSTERS = load_data()

