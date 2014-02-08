from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.achievement.models import Achievement, AchievementCondition

class AchievementResources(resources.ModelResource):
    class Meta:
        model = Achievement


class AchievementConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)


class AchievementAdmin(ImportExportModelAdmin):
    list_display = ('id', 'tp', 'tp_name', 'des',
    'condition', 'condition_value',
    'sycee', 'buff_tp', 'buff_name', 'buff_value'
    )
    list_filter = ('condition',)

    resource_class = AchievementResources

admin.site.register(AchievementCondition, AchievementConditionAdmin)
admin.site.register(Achievement, AchievementAdmin)

