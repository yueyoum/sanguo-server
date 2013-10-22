# about Crypto module: https://www.dlitz.net/software/pycrypto/doc/
from base64 import b64encode, b64decode
import time

from Crypto.Cipher import AES
from Crypto import Random

from django.conf import settings


class BadEncryptedText(Exception):
    pass

class ExpiredText(Exception):
    pass

BLOCK_SIZE = 16
KEY = settings.CRYPTO_KEY or Random.get_random_bytes(BLOCK_SIZE)
PREFIX = settings.CRYPTO_PREFIX or Random.get_random_bytes(4)


def encrypt(text, key=KEY, prefix=PREFIX):
    prefix = prefix.replace('|', '_')
    text = '%s|%s|' % (prefix, text) 
    length = len(text)
    a, b = divmod(length, BLOCK_SIZE)
    rest = (a + 1) * BLOCK_SIZE - length

    text = '%s%s' % (text, rest * ' ')

    obj = AES.new(key, AES.MODE_ECB)
    res = obj.encrypt(text)
    return b64encode(res)


def decrypt(text, key=KEY, prefix=PREFIX):
    try:
        text = b64decode(text)
    except TypeError:
        raise BadEncryptedText()

    if len(text) % BLOCK_SIZE != 0:
        raise BadEncryptedText()

    obj = AES.new(key, AES.MODE_ECB)
    result = obj.decrypt(text)

    prefix = prefix.replace('|', '_')
    if not result.startswith(prefix):
        raise BadEncryptedText()

    head, tail = result.rsplit('|', 1)
    p, real_text = head.split('|', 1)
    return real_text


def encrypt_with_expire(text, key=KEY, prefix=PREFIX):
    expire = int(time.time())
    return encrypt('%s|%d' % (text, expire), key=key, prefix=prefix)

def decrypt_with_expire(text, expire_in, key=KEY, prefix=PREFIX):
    result = decrypt(text, key=key, prefix=prefix)
    real_text, start_at = result.rsplit('|', 1)
    if int(time.time()) > int(start_at) + expire_in:
        raise ExpiredText()

    return real_text


