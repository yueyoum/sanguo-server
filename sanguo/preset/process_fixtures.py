# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/29/14'

import os
import json

SELF_PATH = os.path.dirname(os.path.realpath(__file__))

def process_errormsg(in_file, out_file):
    with open(in_file, 'r') as f:
        content = json.loads(f.read())

    data = []
    for c in content:
        error_id = c['pk']
        error_index = c['fields']['error_index']
        text = '{0} = {1}\n'.format(error_index, error_id)
        data.append(text)

    with open(out_file, 'w') as f:
        f.writelines(data)


def process_errormsg_zh(in_file, out_file):
    lines = []
    lines.append("# -*- coding: utf-8 -*-\n\n")
    lines.append("ERRORMSGZH = {\n")

    with open(in_file, 'r') as f:
        content = json.loads(f.read())

    for c in content:
        error_id = c['pk']
        error_zh = c['fields']['text_zh'].encode('utf-8')
        lines.append('    {0}: "{1}",\n'.format(error_id, error_zh))

    lines.append("}\n\n")

    with open(out_file, 'w') as f:
        f.writelines(lines)


if __name__ == '__main__':
    errormsg_in = os.path.join(SELF_PATH, 'fixtures', 'errormsg.json')
    errormsg_out = os.path.join(SELF_PATH, 'errormsg.py')
    process_errormsg(errormsg_in, errormsg_out)

    errormsg_zh_out = os.path.join(SELF_PATH, 'errormsg_zh.py')
    process_errormsg_zh(errormsg_in, errormsg_zh_out)

