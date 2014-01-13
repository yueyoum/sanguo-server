# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/13/14'

from django.contrib import admin
from apps.character.models import Character

class CharacterAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'account_id', 'server_id', 'name', 'gold', 'sycee',
        'level', 'exp', 'UpdateNeedsExp', 'official', 'off_exp', 'renown',
        'score_day', 'score_week'
    )

    ordering = ('-id', )
    list_filter = ('account_id', 'server_id', )

    def UpdateNeedsExp(self, obj):
        return obj.update_needs_exp()
    UpdateNeedsExp.short_description = "升级所需经验"

admin.site.register(Character, CharacterAdmin)
