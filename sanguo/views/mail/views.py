# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from core.mail import Mail
from core.attachment import standard_drop_to_attachment_protomsg
from utils.decorate import message_response
from utils import pack_msg

from protomsg import GetAttachmentResponse

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
    attachment = m.get_attachment(mail_id)

    response = GetAttachmentResponse()
    response.ret = 0
    response.attachment.MergeFrom(standard_drop_to_attachment_protomsg(attachment))
    return pack_msg(response)
