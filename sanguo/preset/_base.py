import os

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(CURRENT_PATH, 'data')

LINE_SEP = "\r\n"

def data_path(filename):
    return os.path.join(CURRENT_PATH, 'data', filename)

