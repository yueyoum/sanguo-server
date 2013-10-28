import base64

from protomsg import Formation


def _default_formation():
    account = 3
    hero_ids = [0, 0, 0, 0, 0, 0, 0, 0, 0]


    f = Formation()
    f.account = account
    f.hero_ids.extend(hero_ids)

    data = f.SerializeToString()
    return base64.b64encode(data)


FORMATION = _default_formation()

