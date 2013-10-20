import crypto

def test_crypto_with_right_case():
    original = 'abcd:1234:)()xxx'
    text = crypto.encrypt(original)
    assert crypto.decrypt(text) == original

def test_decrypt_with_invalid_text():
    try:
        crypto.decrypt('adinfe3920:2323')
    except crypto.BadEncryptedText:
        pass
    else:
        raise Exception("Decrypt a random string with NO error")


def test_crypto_expire_with_right_case():
    original = 'abcd:1234:)()xxx'
    text = crypto.encrypt_with_expire(original)
    assert crypto.decrypt_with_expire(text, 1) == original

def test_decrypt_expire_with_invalid_text():
    try:
        crypto.decrypt_with_expire('092:daf.dae.<d', 1)
    except crypto.BadEncryptedText:
        pass
    else:
        raise Exception("Decrypt a random string with NO error")


def test_crypto_expire_with_expired():
    import time

    original = 'abcd:1234:)()xxx'
    text = crypto.encrypt_with_expire(original)
    time.sleep(2)
    
    try:
        crypto.decrypt_with_expire(text, 1)
    except crypto.ExpiredText:
        pass
    else:
        raise Exception("Decrypt an expired text with NO error")

