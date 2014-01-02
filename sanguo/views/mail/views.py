# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from django.http import HttpResponse

from core.mail import Mail
from utils import pack_msg

import protomsg


def open(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.open(mail_id)

    response = protomsg.OpenMailResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def delete(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.delete(mail_id)

    response = protomsg.DeleteMailResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def get_attachment(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.get_attachment(mail_id)

    response = protomsg.GetAttachmentResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')