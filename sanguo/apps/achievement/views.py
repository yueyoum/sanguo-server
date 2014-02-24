
from utils.decorate import message_response

from core.achievement import Achievement
@message_response("AchievementGetRewardResponse")
def get_reward(request):
    req = request._proto
    ach = Achievement(request._char_id)
    ach.get_reward(req.id)
    return None