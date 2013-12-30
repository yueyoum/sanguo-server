# -*- coding: utf-8 -*-
import json
from _base import data_path

LINE_SEP = "\n"


def load_data():
    with open(data_path('stage.json'), 'r') as f:
        content = json.loads(f.read())

    def _parse_warriors(text):
        res = []

        text = text.strip(LINE_SEP)
        for line in text.split(LINE_SEP):
            line.strip(',')
            row = [int(i) for i in line.split(',')]
            res.extend(row)

        return res


    data = {}
    for c in content:
        fields = c["fields"]
        fields["monsters"] = _parse_warriors(fields.pop("warriors"))
        data[c["pk"]] = fields

    return data


def load_drop_data():
    with open(data_path('stage_drop.json'), 'r') as f:
        content = json.loads(f.read())

    #data = {
    #    group_id: {
    #        4: [ 装备
    #            (tid, level, prob, min_amount, max_amount),
    #            ...
    #        ],
    #        5: [ 宝石
    #            (level, prob, min_amount, max_amount)
    #        ]
    #    },
    #    
    #    group_id: {...},
    #    ...
    #}

    data = {}
    for c in content:
        fields = c['fields']
        group_id = fields['group_id']
        this_group_id_data = data.get(group_id, {})

        tp = fields['tp']
        if tp not in [4, 5]:
            raise Exception("load_drop_data, Unkown tp: %d" % tp)

        this_group_tp_data = this_group_id_data.get(tp, [])
        if tp == 4:
            this_group_tp_data.append(
                (
                    fields['tid'],
                    fields['level'],
                    fields['prob'],
                    fields['min_amount'],
                    fields['max_amount']
                )
            )
        else:
            this_group_tp_data.append(
                (
                    fields['level'],
                    fields['prob'],
                    fields['min_amount'],
                    fields['max_amount']
                )
            )

        this_group_id_data[tp] = this_group_tp_data
        data[group_id] = this_group_id_data

    return data


STAGE = load_data()
STAGE_DROP = load_drop_data()


