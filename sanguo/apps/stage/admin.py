# -*- coding: utf-8 -*-

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.stage.models import Battle, Stage, StageDrop, EliteStage

class BattleResources(resources.ModelResource):
    class Meta:
        model = Battle

class StageResources(resources.ModelResource):
    class Meta:
        model = Stage

class StageDropResources(resources.ModelResource):
    class Meta:
        model = StageDrop

class EliteStageResources(resources.ModelResource):
    class Meta:
        model = EliteStage


class BattleAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'level_limit',)
    resource_class = BattleResources

class StageAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'des', 'bg', 'level', 'battle',
        'open_condition', 'Monsters',
        'normal_exp', 'normal_gold', 'normal_drop',
        'first_exp', 'first_gold', 'first_drop',
        'star_exp', 'star_gold', 'star_drop',
    )

    list_filter = ('battle',)
    resource_class = StageResources

    def Monsters(self, obj):
        monsters = obj.monsters.split(',')
        text = []
        for i in range(0, 9, 3):
            text.append(','.join(monsters[i: i+3]))

        return "<br />".join(text)
    Monsters.allow_tags = True
    Monsters.short_description = "怪物ID"


class StageDropAdmin(ImportExportModelAdmin):
    list_display = ('id', 'drops')
    resource_class = StageDropResources


class EliteStageAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'bg', 'level', 'times',
        'open_condition', 'Monsters',
        'normal_exp', 'normal_gold', 'normal_drop',
    )

    resource_class = EliteStageResources

    def Monsters(self, obj):
        monsters = obj.monsters.split(',')
        text = []
        for i in range(0, 9, 3):
            text.append(','.join(monsters[i: i+3]))

        return "<br />".join(text)
    Monsters.allow_tags = True
    Monsters.short_description = "怪物ID"




admin.site.register(Battle, BattleAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(StageDrop, StageDropAdmin)
admin.site.register(EliteStage, EliteStageAdmin)
