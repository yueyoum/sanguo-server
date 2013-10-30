from core.functional import encode_formation_with_raw_data

def _default_formation():
    count = 3
    hero_ids = [0] * 9

    return encode_formation_with_raw_data(count, hero_ids)

DEFAULT_FORMATION = _default_formation()

