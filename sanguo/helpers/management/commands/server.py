# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-8'

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """server stuffs. args:
    check   check redis, mongodb, hub connections. register server
    status  output player amount, active player amount.
    """

    def handle(self, *args, **options):
        if not args:
            self.stdout.write(self.help)
            return

        if args[0] == 'check':
            self._cmd_check()
        elif args[0] == 'status':
            self._cmd_status()
        else:
            self.stdout.write(self.help)

    def _cmd_check(self):
        from core.drives import redis_client
        from startup import main

        redis_client.ping()
        main()

    def _cmd_status(self):
        from core.mongoscheme import MongoCharacter
        from core.activeplayers import ActivePlayers

        total_amount = MongoCharacter.objects.count()
        active_amount = ActivePlayers().amount
        self.stdout.write("Total amount {0}. Active amount {1}".format(total_amount, active_amount))
