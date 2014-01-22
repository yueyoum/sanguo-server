from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.hero.models import Hero, Monster

class HeroResources(resources.ModelResource):
    class Meta:
        model = Hero

class MonsterResources(resources.ModelResource):
    class Meta:
        model = Monster

class HeroAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'avatar', 'image',
        'tp', 'tp_name', 'country', 'country_name',
        'gender', 'gender_name',
        'special_equip_id', 'special_addition',
        'quality', 'quality_name',
        'contribution',
        'attack_growing', 'defense_growing', 'hp_growing',
        'crit', 'dodge', 'skills',
    )

    list_filter = (
        'tp_name', 'country_name', 'gender_name', 'quality_name'
    )
    resource_class = HeroResources


class MonsterAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'avatar', 'image',
        'level', 'attack', 'defense', 'hp', 'crit', 'dodge',
        'skills'
    )

    resource_class = MonsterResources


admin.site.register(Hero, HeroAdmin)
admin.site.register(Monster, MonsterAdmin)
