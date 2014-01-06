class SanguoException(Exception):
    def __init__(self, error_id):
        self.error_id = error_id
        Exception.__init__(self)


class CounterOverFlow(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 20)


class BadMessage(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 1)


class InvalidOperate(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 2)


class CharNotFound(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 3)



class GoldNotEnough(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 10)


class SyceeNotEnough(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 11)


class RenownNotEnough(SanguoException):
    def __init__(self):
        SanguoException.__init__(self, 12)