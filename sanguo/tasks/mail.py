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

    data = json.loads(args['data'])

    name = data['name']
    content = data['content']
    create_at = data['create_at']
    attachment = data['attachment']
    char_ids = data['char_ids']

    if not char_ids:
        char_ids = [c.id for c in MongoCharacter.objects.all()]

    for cid in char_ids:
        m = Mail(cid)
        m.add(name, content, create_at=create_at, attachment=attachment)
