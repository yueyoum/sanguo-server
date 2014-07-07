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

    char_ids = data.get('char_id', None)
    if char_ids:
        cids = char_ids
    else:
        chars = MongoCharacter.objects.all()
        cids = [c.id for c in chars]

    mail_name = data['mail']['name']
    mail_content = data['mail']['content']
    mail_send_at = data['mail']['send_at']
    attachment = json.dumps(data['mail']['attachment'])

    for cid in cids:
        m = Mail(cid)
        m.add(mail_name, mail_content, mail_send_at, attachment)

    return {'ret': 0}
