# -*- coding: utf-8 -*-
#!/usr/bin/env python

__author__ = 'Wang Chao'
__date__ = '1/17/14'


from django.core.management import call_command

def run():
    call_command('loaddata', 'servers.json')
    call_command('loaddata', 'heros.json')
    call_command('loaddata', 'stuff.json')
    call_command('loaddata', 'gems.json')
    call_command('loaddata', 'equipment.json')

if __name__ == '__main__':
    run()
