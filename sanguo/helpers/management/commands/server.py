# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-8'

from django.core.management.base import BaseCommand
from core.server import server

class Command(BaseCommand):
    help = """server stuffs. args:
    check   check redis, mongodb, hub connections. register server
    status  output player amount, active player amount.
    down    make server down
    up      make server up
    """

    def handle(self, *args, **options):
        if not args:
            self.stdout.write(self.help)
            return

        if args[0] == 'check':
            self._cmd_check()
        elif args[0] == 'status':
            self._cmd_status()
        elif args[0] == 'down':
            self._cmd_down()
        elif args[0] == 'up':
            self._cmd_up()
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
        self.stdout.write("Active: {0}. Total amount {1}. Active amount {2}".format(server.active, total_amount, active_amount))


    def _cmd_down(self):
        from utils.api import api_server_change
        api_server_change(data={'server_id': server.id, 'status': 4})


    def _cmd_up(self):
        from utils.api import api_server_change
        api_server_change(data={'server_id': server.id, 'status': 1})

