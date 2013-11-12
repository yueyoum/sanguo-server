from core.drives import mongodb_client_db

def get_char_formation(char_id):
    char_formation_record = mongodb_client_db.char_formation.find_one(
            {'_id': char_id},
            {'_id': 0}
            )
    return char_formation_record['data']

