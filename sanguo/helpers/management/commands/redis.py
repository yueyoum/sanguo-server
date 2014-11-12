# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-12'

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """redis maintain. args:
    dumps   persistence the important data to mongodb
    loads   loads the data from mongodb to redis
    """

    def handle(self, *args, **options):
        if not args:
            self.stdout.write(self.help)
            return

        if args[0] == 'dumps':
            self._cmd_dumps()
        elif args[0] == 'loads':
            self._cmd_loads()
        else:
            self.stdout.write(self.help)

    def _cmd_dumps(self):
        from core.support import RedisPersistence

        RedisPersistence.all_dumps()
        self.stdout.write("Dumps Done. {0} objects".format(len(RedisPersistence.get_subclasses())))

    def _cmd_loads(self):
        from core.support import RedisPersistence

        RedisPersistence.all_loads()
        self.stdout.write("Loads Done. {0} objects".format(len(RedisPersistence.get_subclasses())))

