# -*- coding: utf-8 -*-

from django.contrib import admin
from apps.skill.models import Effect, Skill, SkillEffect


class EffectAdmin(admin.ModelAdmin):
    list_display =  (
        'id', 'name', 'des', 'buff_icon', 'special'
    )

class SkillEffectInline(admin.TabularInline):
    model = SkillEffect
    extra = 1

class SkillAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'des', 'special',
        'mode', 'mode_name', 'prob'
    )
    inlines = [SkillEffectInline,]

admin.site.register(Effect, EffectAdmin)
admin.site.register(Skill, SkillAdmin)

