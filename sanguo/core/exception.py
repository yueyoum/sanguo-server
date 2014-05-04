import logging
from django.conf import settings
from utils.timezone import localnow

logger = logging.getLogger('sanguo')

NODE_ID = settings.NODE_ID

class SanguoException(Exception):
    def __init__(self, error_id, char_id, func_name, error_msg=""):
        self.error_id = error_id
        self.error_msg = error_msg

        extra = {
            'node_id': NODE_ID,
            'error_id': error_id,
            'char_id': char_id,
            'func_name': func_name,
            'error_msg': error_msg,
            'occurred_at': localnow().strftime('%Y-%m-%d %H:%M:%S'),
        }

        logger.debug("Node: {0}. Error_id: {1}. Char_id: {2}. Func_name: {3}. Msg: {4}".format(
            NODE_ID, error_id, char_id, func_name, error_msg),
                    extra=extra
                    )
        Exception.__init__(self)


class CounterOverFlow(Exception):
    pass

