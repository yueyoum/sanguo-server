from mongoengine import DoesNotExist


from core.mongoscheme import MongoCounter
from core.exception import CounterOverFlow
from core.character import Char

from preset.settings import COUNTER
from preset.data import VIP_FUNCTION


class Counter(object):
    __slots__ = ['char_id', 'func_name']
    def __init__(self, char_id, func_name):
        self.char_id = char_id
        self.func_name = func_name
        try:
            self.c = MongoCounter.objects.get(id=self.char_id)
        except DoesNotExist:
            self.c = MongoCounter(id=self.char_id)
            self.c.counter = {k: 0 for k in COUNTER.keys()}
            self.c.save()

    @property
    def max_value(self):
        value = COUNTER[self.func_name]
        if value:
            return value

        char = Char(self.char_id).mc
        vip = VIP_FUNCTION[char.vip]
        return getattr(vip, self.func_name)

    @property
    def cur_value(self):
        return self.c.counter.get(self.func_name, 0)

    @property
    def remained_value(self):
        value = self.max_value - self.cur_value
        return value if value >=0 else 0

    def incr(self, value=1):
        if self.remained_value < value:
            raise CounterOverFlow()

        self.c.counter[self.func_name] = self.c.counter.get(self.func_name, 0) + value
        self.c.save()

    def reset(self):
        self.c.counter[self.func_name] = 0
        self.c.save()


class ActivityStageCount(Counter):
    __slots__ = ['char_id', 'func_name']
    def __init__(self, char_id):
        super(ActivityStageCount, self).__init__(char_id, None)

    def make_func_name(self, tp):
        self.func_name = 'activity_stage_{0}'.format(tp)

    @property
    def max_value(self):
        return 3

