# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from core.mail import Mail
from utils.decorate import message_response


@message_response("OpenMailResponse")
def open(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.open(mail_id)
    return None


@message_response("DeleteMailResponse")
def delete(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.delete(mail_id)
    return None


@message_response("GetAttachmentResponse")
def get_attachment(request):
    mail_id = request._proto.id
    m = Mail(request._char_id)
    m.get_attachment(mail_id)
    return None
