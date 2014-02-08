
from utils.decorate import message_response
from core.task import Task


@message_response("TaskGetRewardResponse")
def get_reward(request):
    req = request._proto
    t = Task(request._char_id)
    t.get_reward(req.id)
    return None
