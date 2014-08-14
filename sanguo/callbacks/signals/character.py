from core.signals import char_level_up_signal, char_official_up_signal, char_gold_changed_signal, char_sycee_changed_signal
from core.notify import update_hero_notify
from core.hero import Hero, char_heros_dict
from core.achievement import Achievement
from core.stage import ActivityStage



def _char_level_up(char_id, new_level, **kwargs):
    heros_dict = char_heros_dict(char_id)

    achievement = Achievement(char_id)
    achievement.trig(18, new_level)

    heros = []
    for hid in heros_dict.keys():
        h = Hero(hid)
        h.save_cache()
        heros.append(h)

    update_hero_notify(char_id, heros)

    activity_stage = ActivityStage(char_id)
    activity_stage.check(new_level)


def _char_official_up(char_id, new_official, **kwargs):
    achievement = Achievement(char_id)
    achievement.trig(19, new_official)


def _char_gold_changed(char_id, now_value, change_value, **kwargs):
    if change_value < 0:
        achievement = Achievement(char_id)
        achievement.trig(32, abs(change_value))


def _char_sycee_changed(char_id, now_value, change_value, **kwargs):
    if change_value < 0:
        achievement = Achievement(char_id)
        achievement.trig(31, abs(change_value))


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

