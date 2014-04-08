# -*- coding: utf-8 -*-

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.hero.models import Hero, Monster

class HeroResources(resources.ModelResource):
    class Meta:
        model = Hero

class MonsterResources(resources.ModelResource):
    class Meta:
        model = Monster


class HeroAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'Avatar', 'Image',
        'tp', 'tp_name', 'country', 'country_name',
        'gender', 'gender_name',
        'special_equip_cls', 'special_addition',
        'quality', 'quality_name',
        'grade',
        'contribution',
        'attack_growing', 'defense_growing', 'hp_growing',
        'crit', 'dodge', 'skills', 'default_skill',
        'anger',
    )

    list_filter = (
        'tp_name', 'country_name', 'gender_name', 'quality_name'
    )
    resource_class = HeroResources

    def Avatar(self, obj):
        if not obj.avatar:
            return 'None'
        return u'<img src="/images/hero/avatar/{0}.png" />'.format(obj.avatar)
    Avatar.allow_tags = True

    def Image(self, obj):
        if not obj.image:
            return 'None'
        return u'<a href="/images/hero/image/{0}.jpg" target=_blank><img src="/images/hero/image/{0}.jpg" width="80" /></a>'.format(obj.image)
    Image.allow_tags = True


class MonsterAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'Image',
        'tp', 'tp_name', 'quality',
        'attack', 'defense', 'hp', 'crit', 'dodge',
        'skills', 'default_skill', 'anger',
    )

    resource_class = MonsterResources


    def Image(self, obj):
        if not obj.image:
            return 'None'
        return u'<a href="/images/hero/image/{0}.jpg" target=_blank><img src="/images/hero/image/{0}.jpg" width="80" /></a>'.format(obj.image)
    Image.allow_tags = True



admin.site.register(Hero, HeroAdmin)
admin.site.register(Monster, MonsterAdmin)
