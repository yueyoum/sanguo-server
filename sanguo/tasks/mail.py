# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       mail
Date Created:   2015-08-17 18:23
Description:

"""

import uwsgidecorators

@uwsgidecorators.spool
def send_mail(name, content, create_at, attachment, char_ids=None):
    from core.mongoscheme import MongoCharacter
    from core.mail import Mail

    if not char_ids:
        char_ids = [c.id for c in MongoCharacter.objects.all()]

    for cid in char_ids:
        m = Mail(cid)
        m.add(name, content, create_at=create_at, attachment=attachment)
