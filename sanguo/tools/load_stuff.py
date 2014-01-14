import csv
from apps.item.models import Stuff


def run():
    f = open('/tmp/x.csv')
    reader = csv.reader(f)
    for id, icon, name, des in reader:
        print id, icon, name, des
        Stuff.objects.create(
                id=int(id),
                icon=int(icon) if icon else None,
                name=name,
                des=des
                )




