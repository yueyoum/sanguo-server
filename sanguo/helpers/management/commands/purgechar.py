# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-8-13'

from django.core.management.base import BaseCommand
from core.mongoscheme import purge_char

class Command(BaseCommand):
    help = """Purge Character. args: char id [Int]"""

    def handle(self, *args, **options):
        if not args:
            self.stdout.write(self.help)
            return

        try:
            char_id = int(args[0])
        except:
            self.stdout.write(self.help)
            return

        purge_char(char_id)
