import re

PATTERN = re.compile('\<protocol\s+name="([a-zA-Z]+(?:Response|Notify))"\s+type="(\d+)".+\>')

msg_type = []
msg_type.append("MSG_TYPE = {\n")

for line in file('protobuf/define.xml'):
    x = PATTERN.search(line)
    if not x:
        continue

    _msg, _type = x.groups()
    msg_type.append('    "{0}": {1},\n'.format(_msg, _type))

msg_type.append("}\n")

with open('msg/__init__.py', 'w') as f:
    f.writelines(msg_type)

