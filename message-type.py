import os
import re
import glob

def import_all_protos(msg_path, des):
    protos = glob.glob(os.path.join(msg_path, '*_pb2.py'))

    texts = []
    for p in protos:
        p = os.path.basename(p)
        name = p.rstrip('.py')
        texts.append("from {0} import *\n".format(name))

    texts.append("\n")
    with open(des, 'a') as f:
        f.writelines(texts)



def set_response_notify_type(xml_src, des):
    PATTERN = re.compile('\<protocol\s+name="([a-zA-Z]+(?:Response|Notify))"\s+type="(\d+)".+\>')

    msg_type = []
    msg_type.append("RESPONSE_NOTIFY_TYPE = {\n")

    for line in file(xml_src):
        x = PATTERN.search(line)
        if not x:
            continue

        _msg, _type = x.groups()
        msg_type.append('    "{0}": {1},\n'.format(_msg, _type))

    msg_type.append("}\n\n")

    with open(des, 'a') as f:
        f.writelines(msg_type)


def set_request_type(xml_src, des):
    PATTERN = re.compile('\<protocol\s+name="([a-zA-Z]+Request)"\s+type="(\d+)".+?method="((?:0|1))".+\>')

    msg_type = []
    msg_type.append("REQUEST_TYPE = {\n")

    msg_type_rev = []
    msg_type_rev.append("REQUEST_TYPE_REV = {\n")

    for line in file(xml_src):
        x = PATTERN.search(line)
        if not x:
            continue

        _msg, _type, _method = x.groups()
        _method = "POST" if _method == "1" else "GET"
        msg_type.append(
                '    {0}: ["{1}", "{2}"],\n'.format(_type, _msg, _method)
                )
        msg_type_rev.append(
                '    "{0}": {1},\n'.format(_msg, _type)
                )

    msg_type.append("}\n\n")
    msg_type_rev.append("}\n\n")

    with open(des, 'a') as f:
        f.writelines(msg_type)
        f.writelines(msg_type_rev)


if __name__ == '__main__':
    self_path = os.path.dirname(os.path.realpath(__file__))

    xml_src = os.path.join(self_path, 'protobuf', 'define.xml')
    msg_path = os.path.join(self_path, 'msg')
    des = os.path.join(msg_path, '__init__.py')

    with open(des, 'w'):
        pass

    import_all_protos(msg_path, des)
    set_response_notify_type(xml_src, des)
    set_request_type(xml_src, des)

