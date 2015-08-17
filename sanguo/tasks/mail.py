# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       mail
Date Created:   2015-08-17 18:23
Description:

"""
import json
import uwsgidecorators

@uwsgidecorators.spool
def send_mail(args):
    from core.mongoscheme import MongoCharacter
    from core.mail import Mail

    name = args['name']
    content = args['content']
    create_at = args['create_at']
    attachment = args['attachment']
    char_ids = json.loads(args['char_ids'])

    if not char_ids:
        char_ids = [c.id for c in MongoCharacter.objects.all()]

    for cid in char_ids:
        m = Mail(cid)
        m.add(name, content, create_at=create_at, attachment=attachment)
