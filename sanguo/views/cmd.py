from django.http import HttpResponse

from core.attachment import make_standard_drop_from_template
from core.resource import Resource
from core.functionopen import FunctionOpen
from core.union.member import Member

from preset.data import HEROS, EQUIPMENTS, GEMS, STUFFS, HORSE

def cmd(request):
    req = request._proto
    char_id = request._char_id

    if req.action == 2:
        print "Unsupported"
        return HttpResponse('', content_type='text/plain')

    drop = make_standard_drop_from_template()
    if req.tp == 1:
        drop['exp'] = req.param
    elif req.tp == 2:
        drop['official_exp'] = req.param
    elif req.tp == 3:
        drop['gold'] = req.param
    elif req.tp == 4:
        drop['sycee'] = req.param

    elif req.tp == 5:
        if req.param not in EQUIPMENTS:
            return HttpResponse('', content_type='text/plain')
        drop['equipments'].append((req.param, 1, 1))

    elif req.tp == 6:
        if req.param not in GEMS:
            return HttpResponse('', content_type='text/plain')
        drop['gems'].append((req.param, 1))

    elif req.tp == 7:
        if req.param not in HEROS:
            return HttpResponse('', content_type='text/plain')
        drop['heros'].append((req.param, 1))

    elif req.tp == 8:
        if req.param not in STUFFS:
            return HttpResponse('', content_type='text/plain')
        drop['stuffs'].append((req.param, 1))

    elif req.tp == 9:
        if req.param not in HEROS:
            return HttpResponse('', content_type='text/plain')
        drop['souls'].append((req.param, 1))

    elif req.tp == 10:
        drop['purchase_got'] = req.param
        drop['purchase_actual_got'] = req.param

    elif req.tp == 12:
        if req.param not in HORSE:
            return HttpResponse('', content_type='text/plain')
        drop['horses'].append((req.param, 1))

    elif req.tp == 13:
        Member(char_id).add_coin(req.param)


    resource = Resource(char_id, "CMD", "tp: {0}, param: {1}".format(req.tp, req.param))
    standard_drop = resource.add(**drop)
    print standard_drop

    if req.tp == 11:
        fo = FunctionOpen(char_id)
        fo._open_all()
        fo.send_notify()

    return HttpResponse('', content_type='text/plain')
