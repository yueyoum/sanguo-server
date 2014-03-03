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
        'id', 'name', 'des', 'cast_effect', 'hit_effect', 'is_fullscreen',
        'mode', 'mode_name', 'prob', 'trig_start', 'trig_cooldown',
        'anger_self', 'anger_self_team', 'anger_rival_team',
    )
    inlines = [SkillEffectInline,]
    list_filter = ('mode_name',)

admin.site.register(Effect, EffectAdmin)
admin.site.register(Skill, SkillAdmin)

