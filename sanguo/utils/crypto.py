# about Crypto module: https://www.dlitz.net/software/pycrypto/doc/

from Crypto.Cipher import AES
from Crypto import Random

class BadEncryptedText(Exception):
    pass

BLOCK_SIZE = 16
KEY = Random.get_random_bytes(BLOCK_SIZE)
PREFIX = Random.get_random_bytes(4)


def encrypt(text, key=KEY, prefix=PREFIX):
    prefix = prefix.replace('|', '_')
    text = '%s|%s|' % (prefix, text) 
    length = len(text)
    a, b = divmod(length, BLOCK_SIZE)
    rest = (a + 1) * BLOCK_SIZE - length

    text = '%s%s' % (text, rest * ' ')

    obj = AES.new(key, AES.MODE_ECB)
    return obj.encrypt(text)


def decrypt(text, key=KEY, prefix=PREFIX):
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

if __name__ == '__main__':
    text = 'abcd:893s'
    result = encrypt(text)
    assert decrypt(result) == text

