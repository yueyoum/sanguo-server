from Crypto.Cipher import DES

from django.conf import settings

class BadEncryptedText(Exception):
    pass



def encrypt(text, key=settings.SANGUO_CRYPTO_KEY, prefix=settings.SANGUO_CRYPTO_PREFIX):
    prefix = prefix.replace('|', '_')
    text = '%s|%s|' % (prefix, text) 
    length = len(text)
    a, b = divmod(length, 8)
    rest = (a + 1) * 8 - length

    text = '%s%s' % (text, rest * ' ')

    obj = DES.new(key, DES.MODE_ECB)
    return obj.encrypt(text)


def decrypt(text, key=settings.SANGUO_CRYPTO_KEY, prefix=settings.SANGUO_CRYPTO_PREFIX):
    if len(text) % 8 != 0:
        raise BadEncryptedText()

    obj = DES.new(key, DES.MODE_ECB)
    result = obj.decrypt(text)

    prefix = prefix.replace('|', '_')
    if not result.startswith(prefix):
        raise BadEncryptedText()

    head, tail = result.rsplit('|', 1)
    p, real_text = head.split('|', 1)
    return real_text

