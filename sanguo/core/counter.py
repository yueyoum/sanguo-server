import logging
from mongoengine import DoesNotExist

from core.mongoscheme import MongoCounter
from core.exception import CounterOverFlow
from preset.settings import COUNTER


logger = logging.getLogger('sanguo')


class Counter(object):
    def __init__(self, char_id, func_name):
        self.char_id = char_id
        self.func_name = func_name
        self.key = '{0}.{1}'.format(char_id, func_name)
        try:
            self.c = MongoCounter.objects.get(id=self.key)
        except DoesNotExist:
            self.c = MongoCounter()
            self.c.id = self.key
            self.c.cur_value = 0
            self.c.save()

    @property
    def max_value(self):
        return COUNTER[self.func_name]

    @property
    def cur_value(self):
        return self.c.cur_value

    @property
    def remained_value(self):
        return self.max_value - self.cur_value

    def incr(self, value=1):
        if self.remained_value < value:
            logging.info("Counter. char {0}. {1}. MaxValue: {0}, CurValue: {1}, WannaValue: {2}".format(
                self.char_id, self.func_name, self.max_value, self.cur_value, value
            ))
            raise CounterOverFlow()

        self.c.cur_value += value
        self.c.save()
    
