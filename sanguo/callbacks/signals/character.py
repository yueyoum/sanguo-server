
import arrow

from core.signals import (
    char_level_up_signal,
    char_official_up_signal,
    char_gold_changed_signal,
    char_sycee_changed_signal,
    global_buff_changed_signal,
)

from core.character import Char
from core.notify import update_hero_notify
from core.hero import char_heros_obj
from core.achievement import Achievement
from core.stage import ActivityStage
from core.activity import ActivityStatic
from core.mongoscheme import MongoCostSyceeLog


def _all_hero_changed(char_id):
    heros = char_heros_obj(char_id)
    update_hero_notify(char_id, heros)

def _global_buff_changed(char_id, **kwargs):
    _all_hero_changed(char_id)
    Char(char_id).send_notify()


def _char_level_up(char_id, new_level, **kwargs):
    _all_hero_changed(char_id)

    achievement = Achievement(char_id)
    achievement.trig(18, new_level)
    activity_stage = ActivityStage(char_id)
    activity_stage.check(new_level)

    ActivityStatic(char_id).trig(1001)


def _char_official_up(char_id, new_official, **kwargs):
    achievement = Achievement(char_id)
    achievement.trig(19, new_official)


def _char_gold_changed(char_id, now_value, change_value, **kwargs):
    if change_value < 0:
        achievement = Achievement(char_id)
        achievement.trig(32, abs(change_value))


def _char_sycee_changed(char_id, now_value, cost_value, add_value, **kwargs):
    if cost_value:
        cost_value = abs(cost_value)
        achievement = Achievement(char_id)
        achievement.trig(31, cost_value)

        cslog = MongoCostSyceeLog()
        cslog.char_id = char_id
        cslog.sycee = cost_value
        cslog.cost_at = arrow.utcnow().timestamp
        cslog.save()

        ActivityStatic(char_id).trig(6001)


char_level_up_signal.connect(
    _char_level_up,
    dispatch_uid='callbacks.signals.character._char_level_up'
)

char_official_up_signal.connect(
    _char_official_up,
    dispatch_uid='callbacks.signals.character._char_official_up'
)

char_gold_changed_signal.connect(
    _char_gold_changed,
    dispatch_uid='callbacks.signals.character._char_gold_changed'
)

char_sycee_changed_signal.connect(
    _char_sycee_changed,
    dispatch_uid='callbacks.signals.character._char_sycee_changed'
)

global_buff_changed_signal.connect(
    _global_buff_changed,
    dispatch_uid='callbacks.signals.character._global_buff_changed'
)
