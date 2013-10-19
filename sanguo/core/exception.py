class SanguoViewException(Exception):
    def __init__(self, response_msg_name, error_id):
        self.response_msg_name = response_msg_name
        self.error_id = error_id
        Exception.__init__(self)

