# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

from django.contrib import admin
from apps.item.models import Equipment, Stuff, Gem


class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'IconLarge',
        'step', 'step_name', 'tp', 'tp_name', 'cls', 'cls_name',
        'upgrade_to', 'stuff_needs',
        'attack', 'defense', 'hp',
        'slots', 'gem_addition', 'growing'
    )

    list_filter = ('tp', 'cls', 'step',)

    def Icon(self, obj):
        # TODO
        return ""


    def IconLarge(self, obj):
        # TODO
        return ""



class GemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'icon', 'tp_name', 'level',
        'used_for', 'used_for_name', 'value', 'merge_to'
    )

    list_filter = ('used_for',)

class StuffAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'des', 'buy_sycee', 'sell_gold',
    )

    def Icon(self, obj):
        # TODO
        return ""


admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Gem, GemAdmin)
admin.site.register(Stuff, StuffAdmin)
