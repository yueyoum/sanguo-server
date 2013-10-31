import urllib2
import struct
import base64

from protomsg import REQUEST_TYPE_REV

__all__ = [
        'pack_data',
        'unpack_data',
        'make_request',
        ]


FMT = struct.Struct('>i')
URL = "http://127.0.0.1:8000"

def pack_data(req):
    id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
    data = req.SerializeToString()
    data = '{0}{1}{2}{3}'.format(
            FMT.pack(1), FMT.pack(id_of_msg), FMT.pack(len(data)), data
            )
    return data


def unpack_data(res):
    num_of_msgs = FMT.unpack(res[:4])[0]
    res = res[4:]

    def _unpack(res):
        id_of_msg = FMT.unpack(res[:4])[0]
        res = res[4:]
        len_of_msg = FMT.unpack(res[:4])[0]
        res = res[4:]
        return id_of_msg, len_of_msg, res[:len_of_msg], res[len_of_msg:]

    msgs = []
    for i in range(num_of_msgs):
        id_of_msg, len_of_msg, msg, res = _unpack(res)
        msgs.append((id_of_msg, len_of_msg, msg))

    assert num_of_msgs == len(msgs)
    return msgs

def make_request(path, data, method="POST"):
    if method == "POST":
        url = URL + path
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)
    else:
        url = '%s%s?%s' % (URL, path, base64.urlsafe_b64encode(data))
        response = urllib2.urlopen(url)

    return response.read()

