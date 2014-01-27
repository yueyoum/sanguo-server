import csv
from apps.item.models import Equipment

def run():
    f = open('/tmp/a.csv')
    reader = csv.reader(f)
    for id, name, icon, icon_large, step, step_name, tp, tp_name, cls, cls_name, to, needs, attack, defense, hp, slots, addition, growing in reader:
        print id, name, icon, icon_large, step, step_name, tp, tp_name, cls, cls_name, to , needs, attack, defense, hp, slots, addition, growing
        Equipment.objects.create(
            id=int(id),
            name=name,
            icon=icon,
            icon_large=icon_large,
            step=int(step),
            step_name=step_name,
            tp=int(tp),
            tp_name=tp_name,
            cls=int(cls),
            cls_name=cls_name,
            upgrade_to=int(to) if to else None,
            stuff_needs=needs,
            attack=int(attack) if attack else 0,
            defense=int(defense) if defense else 0,
            hp=int(hp) if hp else 0,
            slots=int(slots),
            gem_addition=float(addition) * 100,
            growing=int(growing),
        )

