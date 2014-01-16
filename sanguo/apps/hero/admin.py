from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.hero.models import Hero

class HeroResources(resources.ModelResource):
    class Meta:
        model = Hero


class HeroAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'avatar', 'image',
        'tp', 'tp_name', 'country', 'country_name',
        'gender', 'gender_name',
        'special_equip_id', 'special_addition',
        'quality', 'quality_name',
        'contribution',
        'attack_growing', 'defense_growing', 'hp_growing',
        'crit', 'dodge', 'skill'
    )

    list_filter = (
        'tp_name', 'country_name', 'gender_name', 'quality_name'
    )
    resource_class = HeroResources



admin.site.register(Hero, HeroAdmin)
