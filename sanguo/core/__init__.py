import os
import ctypes

from django.conf import settings

DLL_FILE = os.path.join(settings.PROJECT_PATH, 'dll', 'sanguo.so')
DLL = ctypes.cdll.LoadLibrary(DLL_FILE)

DLL.hero_attack.restype = ctypes.c_float
DLL.hero_defense.restype = ctypes.c_float
DLL.hero_hp.restype = ctypes.c_float

