import json
import random

from preset._base import data_path

def load_data():
    with open(data_path('hero.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        _id = c["pk"]
        fields = c["fields"]
        fields.pop("name")
        fields.pop("avatar")
        fields.pop("image")
        fields["id"] = _id
        data[_id] = fields

    return data

class _Heros(object):
    def __init__(self):
        self.heros = load_data()

    def get_random_hero_ids(self, num):
        ids = self.heros.keys()
        res = []
        while True:
            if len(res) >= num or not ids:
                break

            this_id = random.choice(ids)
            ids.remove(this_id)

            if this_id not in res:
                res.append(this_id)

        return res

    def get_random_heros(self, num):
        res = self.get_random_hero_ids(num)
        return [self.heros[i] for i in res]

    def get_heros_by_quality(self,quality):
        return [h for h in self.heros.values() if h["quality"] == quality]

    def get_hero_ids_by_quality(self, quality):
        return [h["id"] for h in self.heros.values() if h["quality"] == quality]

    def __getitem__(self, key):
        return self.heros[key]

    def all_ids(self):
        return self.heros.keys()

    def keys(self):
        return self.heros.keys()

    def values(self):
        return self.heros.values()


HEROS = _Heros()


