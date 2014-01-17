# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/17/14'

def run():
    from django.core.management import call_command
    call_command('loaddata', 'servers.json')
    call_command('loaddata', 'heros.json')
    call_command('loaddata', 'stuff.json')
    call_command('loaddata', 'gems.json')
    call_command('loaddata', 'equipment.json')

if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanguo.settings')
    run()
