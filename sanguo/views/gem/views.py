# -*- coding: utf-8 -*

from utils.decorate import message_response

@message_response("MergeGemResponse")
def merge(request):
    req = request._proto
    char_id = request._char_id

    # TODO merge gem
    return None
