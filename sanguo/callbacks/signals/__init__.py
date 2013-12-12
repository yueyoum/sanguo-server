
import os

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

files = os.listdir(CURRENT_PATH)
for f in files:
    if f.endswith('.py') and f != '__init__.py':
        __import__('callbacks.signals.{0}'.format(f[:-3]))

