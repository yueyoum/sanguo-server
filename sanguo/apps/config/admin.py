from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.config.models import CharInit, ArenaReward

class CharInitAdmin(admin.ModelAdmin):
    list_display = (
        'gold', 'sycee',
        'heros', 'gems', 'stuffs'
    )

class ArenaRewardResources(resources.ModelResource):
    class Meta:
        model = ArenaReward

class ArenaRewardAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'day_gold', 'week_gold', 'week_stuffs'
    )

admin.site.register(CharInit, CharInitAdmin)
admin.site.register(ArenaReward, ArenaRewardAdmin)

