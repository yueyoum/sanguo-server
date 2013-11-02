import json

from preset._base import data_path, LINE_SEP


def load_data():
    with open(data_path('get_hero.json'), 'r') as f:
        content = json.loads(f.read())

    def _parse_prob(text):
        text = text.strip(LINE_SEP)
        lines = text.split(LINE_SEP)

        probs = []
        for line in lines:
            line = line.strip(',')
            qid, prob = line.split(',')
            probs.append((int(qid), int(prob)))

        probs.sort(key=lambda item: item[1])
        return probs

    data = {}
    for c in content:
        fields = c["fields"]
        _id = fields.pop("mode")
        fields["prob"] = _parse_prob(fields["quality_and_prob"])

        data[_id] = fields

    return data

GET_HERO = load_data()

