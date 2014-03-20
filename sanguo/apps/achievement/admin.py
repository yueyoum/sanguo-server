from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.achievement.models import Achievement

class AchievementResources(resources.ModelResource):
    class Meta:
        model = Achievement


class AchievementAdmin(ImportExportModelAdmin):
    list_display = ('id', 'tp', 'tp_name', 'name', 'first', 'next', 'des', 'mode',
    'condition_name', 'condition_id', 'condition_value',
    'sycee', 'buff_used_for', 'buff_name', 'buff_value',
    'equipments', 'gems', 'stuffs',
    )

    list_filter = ('mode', 'condition_id',)

    resource_class = AchievementResources

admin.site.register(Achievement, AchievementAdmin)

