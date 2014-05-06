# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/17/14'

import json

from utils.decorate import json_return
from core.mongoscheme import MongoCharacter
from core.mail import Mail


@json_return
def send_mail(request):
    data = request.body
    data = json.loads(data)
    print data

    sid = data.get('server_id', None)
    if sid:
        chars = MongoCharacter.objects.filter(server_id=sid)
        cids = [c.id for c in chars]
    else:
        cids = data.get('char_id', None)
        if not cids:
            return {'ret': 1}

    # mail_id = data['mail']['id']
    mail_name = data['mail']['name']
    mail_content = data['mail']['content']
    mail_send_at = data['mail']['send_at']
    attachment = json.dumps(data['mail']['attachment'])

    for cid in cids:
        m = Mail(cid)
        m.add(mail_name, mail_content, mail_send_at, attachment)

    return {'ret': 0}
