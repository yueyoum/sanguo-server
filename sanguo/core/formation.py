from base64 import b64decode, b64encode

import protomsg


def decode_formation(text):
    msg = getattr(protomsg, "Formation")()
    msg.ParseFromString(b64decode(text))
    return msg

def encode_formation(msg):
    return b64encode(msg.SerializeToString())


def encode_formation_with_raw_data(count, ids):
    msg = getattr(protomsg, "Formation")()
    msg.count = count
    msg.hero_ids.extend(ids)
    return b64encode(msg.SerializeToString())


