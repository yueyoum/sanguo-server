# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/17/14'

import json

from utils.decorate import json_return
from core.attachment import get_drop_from_raw_package

from tasks import mail


@json_return
def send_mail(request):
    data = request.body
    data = json.loads(data)

    mode = data.get('mode', None)
    if mode == 'test':
        print "GOT TEST MAIL"
        return {'ret': 0}

    char_ids = data.get('char_id', None)

    mail_name = data['mail']['name']
    mail_content = data['mail']['content']
    mail_send_at = data['mail']['send_at']

    attachment = data['mail'].get('attachment', '')
    if attachment:
        attachment = json.dumps(
            get_drop_from_raw_package(data['mail']['attachment'])
        )

    arg = {
        'name': mail_name,
        'content': mail_content,
        'create_at': mail_send_at,
        'attachment': attachment,
        'char_ids': char_ids
    }

    mail.send_mail(data=json.dumps(arg))
    return {'ret': 0}
