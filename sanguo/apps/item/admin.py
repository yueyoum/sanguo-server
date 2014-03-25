# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from apps.item.models import Equipment, Stuff, Gem

class EquipmentResources(resources.ModelResource):
    class Meta:
        model = Equipment

class EquipmentAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'IconLarge',
        'step', 'step_name', 'tp', 'tp_name', 'cls', 'cls_name',
        'upgrade_to', 'stuff_needs',
        'attack', 'defense', 'hp',
        'slots', 'gem_addition', 'growing'
    )

    list_filter = ('tp', 'cls', 'step',)
    resource_class = EquipmentResources


    def Icon(self, obj):
        if not obj.icon:
            return 'None'
        return u'<img src="/images/equipment/100/{0}.png" />'.format(obj.icon)
    Icon.allow_tags = True


    def IconLarge(self, obj):
        # TODO
        return ""



class GemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'tp_name', 'level',
        'used_for', 'used_for_name', 'value', 'merge_to',
        'sell_gold',
    )

    list_filter = ('used_for',)


    def Icon(self, obj):
        if not obj.icon:
            return 'None'
        return u'<img src="/images/gem/{0}.png" />'.format(obj.icon)
    Icon.allow_tags = True





class StuffAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'tp', 'value', 'des', 'buy_sycee', 'sell_gold',
    )

    def Icon(self, obj):
        if not obj.icon:
            return 'None'
        return u'<img src="/images/item/{0}.png" />'.format(obj.icon)
    Icon.allow_tags = True

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Gem, GemAdmin)
admin.site.register(Stuff, StuffAdmin)
