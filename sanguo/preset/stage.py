import json
from preset._base import data_path

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
            res.append(row)

        return res


    data = {}
    for c in content:
        fields = c["fields"]
        fields.pop("name")
        fields["monsters"] = _parse_warriors(fields.pop("warriors"))
    
        # TODO drop

        data[c["pk"]] = fields

    return data

STAGE = load_data()


