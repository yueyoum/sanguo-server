import logging
from utils.timezone import localnow

logger = logging.getLogger('sanguo')


class SanguoException(Exception):
    def __init__(self, error_id, char_id, func_name, error_msg=""):
        self.error_id = error_id
        self.error_msg = error_msg

        extra = {
            'log_type_id': 1,
            'error_id': error_id,
            'char_id': char_id,
            'func_name': func_name,
            'error_msg': error_msg,
            'occurred_at': localnow().strftime('%Y-%m-%d %H:%M:%S'),
        }

        logger.debug("Error_id: {0}. Char_id: {1}. Func_name: {2}. Msg: {3}".format(
                    error_id, char_id, func_name, error_msg),
                    extra=extra
                    )
        Exception.__init__(self)


class CounterOverFlow(Exception):
    pass

