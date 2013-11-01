from settings import *

TESTING = True

CRYPTO_KEY = '1234567890abcdef'
CRYPTO_PREFIX= 'ok'

REDIS_DB = 1
MONGODB_DB = 'test_sanguo'

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
