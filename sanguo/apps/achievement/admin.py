from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.achievement.models import Achievement

class AchievementResources(resources.ModelResource):
    class Meta:
        model = Achievement


class AchievementAdmin(ImportExportModelAdmin):
    list_display = ('id', 'tp', 'tp_name', 'name', 'des', 'mode',
    'condition_id', 'condition_name', 'condition_value',
    'sycee', 'buff_id', 'buff_name', 'buff_value'
    )

    resource_class = AchievementResources

admin.site.register(Achievement, AchievementAdmin)

