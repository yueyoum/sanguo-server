# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'


import re
import subprocess

def get_ipv4_address(command_ifconfig='/sbin/ifconfig', interface='eth0'):
    pipe = subprocess.PIPE
    p = subprocess.Popen(command_ifconfig, stdout=pipe, stderr=pipe)
    p.wait()

    out, err = p.communicate()
    if err:
        raise RuntimeError("Error: {0}, {1}".format(command_ifconfig, err))

    pattern = re.compile('inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

    def _find():
        lines = out.split('\n')
        for i in range(len(lines)):
            if lines[i].startswith(interface):
                ipv4_line = lines[i+1]
                return pattern.findall(ipv4_line)[0]
        return None

    ip = _find()
    if not ip:
        raise RuntimeError("Error: Can not find ip")

    return ip


if __name__ == '__main__':
    print get_ipv4_address()

