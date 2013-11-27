from core.mongoscheme import MongoChar

def get_already_stage(char_id):
    stages = MongoChar.objects.only('stages').get(id=char_id).stages
    if not stages:
        return None
    return {int(k): v for k, v in stages.iteritems()}

def get_new_stage(char_id):
    stage_new = MongoChar.objects.only('stage_new').get(id=char_id).stage_new
    return stage_new

