import os
import logging

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
SANGUO_PATH = os.path.dirname(CURRENT_PATH)

os.chdir(SANGUO_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanguo.settings')




