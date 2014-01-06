from core.gem import merge_gem
from utils.decorate import message_response

@message_response("MergeGemResponse")
def merge(request):
    req = request._proto
    char_id = request._char_id

    merge_gem(
        req.id,
        req.amount,
        req.using_sycee,
        char_id
    )
    return None
