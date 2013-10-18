import urllib2
import struct
import base64

from msg import REQUEST_TYPE_REV

__all__ = [
        'pack_data',
        'unpack_data',
        'make_request',
        ]


FMT = struct.Struct('>i')
URL = "http://127.0.0.1:8000"

def pack_data(req):
    id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
    data = FMT.pack(id_of_msg) + req.SerializeToString()
    return data


def unpack_data(res):
    num_of_msgs = FMT.unpack(res[:4])
    res = res[4:]
    id_of_msg = FMT.unpack(res[:4])
    res = res[4:]
    len_of_msg = FMT.unpack(res[:4])
    res = res[4:]
    return num_of_msgs[0], id_of_msg[0], len_of_msg[0], res

def make_request(path, data, method="POST"):
    if method == "POST":
        url = URL + path
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)
    else:
        url = '%s%s?%s' % (URL, path, base64.urlsafe_b64encode(data))
        response = urllib2.urlopen(url)

    return response.read()

