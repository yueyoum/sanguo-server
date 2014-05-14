from django.http import HttpResponse

from core.attachment import make_standard_drop_from_template
from core.resource import Resource

def cmd(request):
    req = request._proto
    char_id = request._char_id

    if req.action == 2:
        print "Unsupported"
        return

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
        drop['equipments'].append((req.param, 1, 1))
    elif req.tp == 6:
        drop['gems'].append((req.param, 1))
    elif req.tp == 7:
        drop['heros'].append((req.param, 1))
    elif req.tp == 8:
        drop['stuffs'].append((req.param, 1))
    elif req.tp == 9:
        drop['souls'].append((req.param, 1))


    resource = Resource(char_id, "CMD")
    standard_drop = resource.add(**drop)
    print standard_drop

    return HttpResponse('', content_type='text/plain')
