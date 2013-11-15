from core.drives import document_char

def get_char_formation(char_id):
    char_formation = document_char.get(char_id, formation=1)
    return char_formation['formation']

