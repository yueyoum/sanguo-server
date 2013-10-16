import struct

from msg import MSG_TYPE

NUM_FIELD = struct.Struct('>i')


def pack_msg(msg):
    binary = msg.SerializeToString()
    id_of_msg = MSG_TYPE[msg.DESCRIPTOR.name]
    len_of_msg = len(binary)

    data = '%s%s%s' % (
            NUM_FIELD.pack(id_of_msg),
            NUM_FIELD.pack(len_of_msg),
            binary
            )

    return data

