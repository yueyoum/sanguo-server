# -*- coding: utf-8 -*
import json
from _base import data_path


def load_data():
    with open(data_path('gem.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        fields = c['fields']
        fields.pop('name')
        merge_condition = fields['merge_condition']
        if merge_condition:
            fields['merge_condition'] = [int(i) for i in merge_condition.split(',')]
        else:
            fields['merge_condition'] = []

        data[c['pk']] = fields

    return data


def organize_by_level(data):
    res = {}
    for k, v in data.iteritems():
        level = v['level']
        this_level_ids = res.get(level, [])
        this_level_ids.append(k)
        res[level] = this_level_ids

    return res


class _Gem(object):
    def __init__(self):
        self.data = load_data()
        self.level_data = organize_by_level(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def get_ids_by_level(self, level):
        return self.level_data[level][:]


GEM = _Gem()
