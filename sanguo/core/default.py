import base64

from protomsg import Formation


def _default_formation():
    position = (
            (1, True, 0), (2, True, 0), (3, False, 0),
            (4, True, 0), (5, True, 0), (6, False, 0),
            (7, True, 0), (8, True, 0), (9, False, 0),
            )

    f = Formation()
    for pos in position:
        p = f.positions.add()
        p.pos, p.enable, p.hero_id = pos

    data = f.SerializeToString()
    return base64.b64encode(data)


FORMATION = _default_formation()

