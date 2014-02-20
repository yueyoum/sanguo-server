# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/17/14'

def run():
    from django.core.management import call_command
    f = open('datatable', 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
        _, fixture = line.split(':')
        fixture = fixture.rstrip('\n')
        call_command('loaddata', fixture)

if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanguo.settings')
    run()
