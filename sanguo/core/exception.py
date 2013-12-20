class SanguoViewException(Exception):
    def __init__(self, error_id, response_msg_name="CommandResponse"):
        self.error_id = error_id
        self.response_msg_name = response_msg_name
        Exception.__init__(self)

class CounterOverFlow(Exception):
    pass
