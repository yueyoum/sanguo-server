
from django import forms

from core.mongoscheme import MongoCharacter
from core.character import Char
from core.union.union import Union, UnionDummy
from core.union.member import Member

from utils.decorate import json_return


@json_return
def character_information(request):
    char_id = int(request.POST['char_id'])
    char = Char(char_id).mc
    return {
        'gold': char.gold,
        'sycee': char.sycee,
        'level': char.level,
        'exp': char.exp,
        'vip': char.vip,
    }

@json_return
def get_joined_union(request):
    char_id = int(request.POST['char_id'])

    union = Union(char_id)
    if isinstance(union, UnionDummy):
        data = None
    else:
        m = Member(char_id)
        data = {
            'char_id': char_id,
            'union': union.union_id,
            'union_owner': union.mongo_union.owner,
            'union_name': union.mongo_union.name,
            'union_bulletin': union.mongo_union.bulletin,
            'union_level': union.mongo_union.level,
            'union_contribute_points': union.mongo_union.contribute_points,
            'union_score': union.mongo_union.score,
            'member_coin': m.mongo_union_member.coin,
            'member_contribute_points': m.mongo_union_member.contribute_points,
            'member_position': m.mongo_union_member.position,
            'member_checkin_times': m.mongo_union_member.checkin_times,
            'member_buy_buff_times': m.mongo_union_member.buy_buff_times,
            'member_boss_times': m.mongo_union_member.boss_times
        }

    return {
        'ret': 0,
        'data': data
    }


class ModifyCharForm(forms.Form):
    char_id = forms.IntegerField(required=True)
    # gold = forms.IntegerField(required=False)
    # sycee = forms.IntegerField(required=False)
    # level = forms.IntegerField(required=False)
    # vip = forms.IntegerField(required=False)
    name = forms.CharField(required=True)
    value = forms.IntegerField(required=True)


@json_return
def character_modify(request):

    form = ModifyCharForm(request.POST)
    if not form.is_valid():
        return {'ret': 1}

    char_id = form.cleaned_data['char_id']
    mongo_char = MongoCharacter.objects.get(id=char_id)
    setattr(mongo_char, form.cleaned_data['name'], form.cleaned_data['value'])
    mongo_char.save()
    return {'ret': 0}

