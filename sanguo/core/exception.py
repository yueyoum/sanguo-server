import logging

logger = logging.getLogger('sanguo')


class SanguoException(Exception):
    def __init__(self, error_id, error_msg=""):
        self.error_id = error_id
        if error_msg:
            logger.info("[EXCEPTION {0}] {1}".format(error_id, error_msg))
        Exception.__init__(self)


class CounterOverFlow(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 20, error_msg)


class BadMessage(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 1, error_msg)


class InvalidOperate(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 2, error_msg)


class CharNotFound(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 3, error_msg)


class GoldNotEnough(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 10, error_msg)


class SyceeNotEnough(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 11, error_msg)


class RenownNotEnough(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 12, error_msg)

class LevelTooLow(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 13, error_msg)

class OfficialTooLow(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 14, error_msg)

class GemNotEnough(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 15, error_msg)

class StuffNotEnough(SanguoException):
    def __init__(self, error_msg=""):
        SanguoException.__init__(self, 16, error_msg)
