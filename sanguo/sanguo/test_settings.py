from settings import *


CRYPTO_KEY = '1234567890abcdef'
CRYPTO_PREFIX= 'ok'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_sanguo',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
