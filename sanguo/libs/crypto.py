# about Crypto module: https://www.dlitz.net/software/pycrypto/doc/
import time

from Crypto.Cipher import AES
# from Crypto import Random
# Random.get_random_bytes(SIZE)

from django.conf import settings


class BadEncryptedText(Exception):
    pass


class ExpiredText(Exception):
    pass


BLOCK_SIZE = 16
MODE = AES.MODE_ECB

KEY = settings.CRYPTO_KEY


def encrypt(text, key=KEY):
    length = len(text)
    a, b = divmod(length, BLOCK_SIZE)
    rest = (a + 1) * BLOCK_SIZE - length - 1

    text = '%s|%s' % (text, rest * '*')

    obj = AES.new(key, MODE)
    return obj.encrypt(text)


def decrypt(text, key=KEY):
    if len(text) % BLOCK_SIZE != 0:
        raise BadEncryptedText()

    obj = AES.new(key, MODE)
    result = obj.decrypt(text)

    head, tail = result.rsplit('|', 1)
    return head


def encrypt_with_expire(text, key=KEY):
    expire = int(time.time())
    return encrypt('%s|%d' % (text, expire), key=key)


def decrypt_with_expire(text, expire_in, key=KEY):
    result = decrypt(text, key=key)
    real_text, start_at = result.rsplit('|', 1)
    if int(time.time()) > int(start_at) + expire_in:
        raise ExpiredText()

    return real_text

