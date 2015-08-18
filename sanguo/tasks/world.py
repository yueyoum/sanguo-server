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
import uwsgi


@uwsgidecorators.spoolraw
def broadcast(args):
    from core.mongoscheme import MongoCharacter
    from core.msgpipe import publish_to_char

    try:
        data = cPickle.loads(args['data'])
        msg = data['msg']

        chars = MongoCharacter._get_collection().find({}, {'_id': 1})
        for c in chars:
            char_id = c['_id']
            publish_to_char(char_id, msg)
    except:
        traceback.print_exc()
    finally:
        return uwsgi.SPOOL_OK

