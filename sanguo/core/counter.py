from mongoengine import DoesNotExist

from core.mongoscheme import MongoCounter
from core.exception import CounterOverFlow
from preset.settings import COUNTER


class Counter(object):
    def __init__(self, char_id, func_name):
        self.char_id = char_id
        self.func_name = func_name
        try:
            self.c = MongoCounter.objects.get(id=self.char_id)
        except DoesNotExist:
            self.c = MongoCounter(id=self.char_id)
            self.c.counter = COUNTER
            self.c.save()

    @property
    def max_value(self):
        return COUNTER[self.func_name]

    @property
    def cur_value(self):
        return self.c.counter[self.func_name]

    @property
    def remained_value(self):
        value = self.max_value - self.cur_value
        return value if value >=0 else 0

    def incr(self, value=1):
        if self.remained_value < value:
            raise CounterOverFlow()

        self.c.counter[self.func_name] += value
        self.c.save()
