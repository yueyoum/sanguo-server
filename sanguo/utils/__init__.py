import struct

from protomsg import RESPONSE_NOTIFY_TYPE

NUM_FIELD = struct.Struct('>i')


class DummyObject(object):
    def __init__(self, v=0):
        self.v = v

    def __getattr__(self, x):
        return self.v


def pack_msg(msg, session=""):
    msg.session = session
    binary = msg.SerializeToString()
    id_of_msg = RESPONSE_NOTIFY_TYPE[msg.DESCRIPTOR.name]
    len_of_msg = len(binary)

    data = '%s%s%s' % (
        NUM_FIELD.pack(id_of_msg),
        NUM_FIELD.pack(len_of_msg),
        binary
    )

    return data

