# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/14/14'

from django.contrib import admin
from apps.item.models import EquipmentClass, Equipment

class EquipmentClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'Icon', 'IconLarge',
        'step', 'tp', 'cls', 'upgrade_to', 'stuff_needs',
        'attack', 'defense', 'hp',
        'slots', 'gem_addition'
    )

    list_filter = ('tp', 'cls', 'step',)

    def Icon(self, obj):
        # TODO
        return ""


    def IconLarge(self, obj):
        # TODO
        return ""

admin.site.register(EquipmentClass, EquipmentClassAdmin)
admin.site.register(Equipment, EquipmentAdmin)
