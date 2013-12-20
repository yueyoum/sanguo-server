from mongoengine import DoesNotExist

from core.settings import COUNTER
from core.mongoscheme import MongoCounter
from core.exception import CounterOverFlow


class Counter(object):
    def __init__(self, char_id, func_name):
        self.key = '{0}.{1}'.format(char_id, func_name)
        try:
            self.c = MongoCounter.objects.get(id=self.key)
        except DoesNotExist:
            self.c = MongoCounter()
            self.c.id = self.key
            self.c.max_value = COUNTER[func_name]
            self.c.cur_value = 0
            self.c.save()
    
    @property
    def max_value(self):
        return self.c.max_value
    
    @property
    def cur_value(self):
        return self.c.cur_value
    
    @property
    def remained_value(self):
        return self.c.max_value - self.c.cur_value
    
    def incr(self, value):
        if self.remained_value < value:
            raise CounterOverFlow()
        
        self.c.cur_value += value
        self.c.save()
    
