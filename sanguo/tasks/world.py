# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       world
Date Created:   2015-08-18 11:01
Description:

"""

import cPickle
import traceback
import uwsgidecorators


@uwsgidecorators.spool
def broadcast(args):
    from core.character import get_char_ids_by_last_login
    from core.msgpipe import publish_to_char

    try:
        data = cPickle.loads(args['data'])
        msg = data['msg']

        char_ids = get_char_ids_by_last_login(limit=5)
        for char_id in char_ids:
            publish_to_char(char_id, msg)
    except:
        traceback.print_exc()
