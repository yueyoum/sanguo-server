from __future__ import absolute_import
from celery.task.control import revoke
from celery.utils.log import  get_task_logger

from django.db import transaction

from apps.server.models import ServerStatus

from core.signals import hang_finished_signal

from worker.celery import app

logger = get_task_logger(__name__)


def cancel(jobid, terminate=False):
    revoke(jobid, terminate=terminate)


@app.task
def send_mail(mail_id, send_type, send_to):
    # TODO
    pass

@app.task
def hang_finish(char_id, seconds):
    hang_finished_signal.send(
        sender=None,
        char_id=char_id,
        actual_seconds=seconds
    )


@app.task
def update_server_status(server_id, char_amount=0, login_times=0,
                         pay_players_amount=0, pay_total=0,
                         pve_times=0, pvp_times=0):
    transaction.set_autocommit(False)
    try:
        try:
            s = ServerStatus.objects.select_for_update().get(server_id=server_id)
        except ServerStatus.DoesNotExist:
            ServerStatus.objects.create(
                server_id=server_id,
                char_amount=char_amount,
                login_times=login_times,
                pay_players_amount=pay_players_amount,
                pay_total=pay_total,
                pve_times=pve_times,
                pvp_times=pvp_times
            )
        else:
            s.char_amount += char_amount
            s.login_times += login_times
            s.pay_players_amount += pay_players_amount
            s.pay_total += pay_total
            s.pve_times += pve_times
            s.pvp_times += pvp_times
            s.save()

        logger.info("Update Server Status Done. Server: {0}".format(server_id))
    finally:
        transaction.set_autocommit(True)
