from utils.log import system_logger

class SanguoException(Exception):
    def __init__(self, error_id, char_id, func_name, error_msg=""):
        self.error_id = error_id
        self.error_msg = error_msg

        system_logger(error_id, char_id, func_name, error_msg)

        Exception.__init__(self)


class CounterOverFlow(Exception):
    pass
