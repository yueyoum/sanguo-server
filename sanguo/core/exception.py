class SanguoViewException(Exception):
    def __init__(self, error_id, response_msg_name="CommandResponse"):
        self.error_id = error_id
        self.response_msg_name = response_msg_name
        Exception.__init__(self)

class CounterOverFlow(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 20, response_msg_name)


class BadMessage(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 1, response_msg_name)
    

class InvalidOperate(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 2, response_msg_name)


class GoldNotEnough(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 10, response_msg_name)


class SyceeNotEnough(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 11, response_msg_name)


class RenownNotEnough(SanguoViewException):
    def __init__(self, response_msg_name):
        SanguoViewException.__init__(self, 12, response_msg_name)