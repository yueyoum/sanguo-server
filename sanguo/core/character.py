from core.drives import mongodb_client_db
from core import GLOBAL

def get_char_formation(char_id):
    char_formation_record = mongodb_client_db.char_formation.find_one(
            {'_id': char_id},
            {'_id': 0}
            )

    if char_formation_record is None:
        old_formation = GLOBAL.DEFAULT_FORMATION
    else:
        old_formation = char_formation_record['data']

    return old_formation

