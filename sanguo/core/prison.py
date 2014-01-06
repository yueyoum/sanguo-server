# -*- coding: utf-8 -*-
from mongoengine import DoesNotExist

from core.mongoscheme import MongoPrison, Prisoner
from timer.tasks import sched
from callbacks import timers
from protomsg import Prisoner as PrisonerProtoMsg
from core.exception import SyceeNotEnough, SanguoException
from core.character import Char

from utils import timezone

from core.signals import prisoner_add_signal
from preset.settings import COST_OPEN_PRISON_SLOT, MAX_PRISON_TRAIN_SLOT, MAX_PRISONERS_AMOUNT


class Prison(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.p = MongoPrison.objects.get(id=self.char_id)
        except DoesNotExist:
            self.p = MongoPrison(id=self.char_id, amount=0)
            self.p.save()

        self.slots = self.p.amount

    @property
    def max_slots(self):
        return MAX_PRISON_TRAIN_SLOT

    @property
    def open_slot_cost(self):
        return COST_OPEN_PRISON_SLOT

    def open_slot(self):
        if self.slots >= self.max_slots:
            raise SanguoException(804)

        c = Char(self.char_id)
        cache_char = c.cacheobj
        if cache_char.sycee < self.open_slot_cost:
            raise SyceeNotEnough()

        self.p.amount += 1
        self.p.save()

        c.update(sycee=-COST_OPEN_PRISON_SLOT)

    @property
    def max_prisoner_amount(self):
        return MAX_PRISONERS_AMOUNT

    def prisoner_full(self):
        return len(self.p.prisoners) >= self.max_prisoner_amount


def save_prisoner(char_id, oid):
    prison = MongoPrison.objects.only('prisoners').get(id=char_id)
    prisoner_ids = [int(i) for i in prison.prisoners.keys()]

    new_persioner_id = 1
    while True:
        if new_persioner_id not in prisoner_ids:
            break
        new_persioner_id += 1

    # FIXME
    job = sched.apply_async(
        [timers.prisoner_job, char_id, new_persioner_id, PrisonerProtoMsg.NOT],
        countdown=60
    )

    p = Prisoner()
    p.id = new_persioner_id
    p.oid = oid
    p.start_time = timezone.utc_timestamp()
    p.status = PrisonerProtoMsg.NOT
    p.jobid = job.id

    prison.prisoners[str(new_persioner_id)] = p
    prison.save()

    prisoner_add_signal.send(
        sender=None,
        char_id=char_id,
        mongo_prisoner_obj=p
    )

    return p