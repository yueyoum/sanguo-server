from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.config.models import CharInit, ArenaReward, Notify, FunctionOpen,  Dialog, DialogStatement

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

    resource_class = ArenaRewardResources


class NotifyResources(resources.ModelResource):
    class Meta:
        model = Notify

class NotifyAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'template', 'des',
    )

    resource_class = NotifyResources

class FunctionOpenAdmin(admin.ModelAdmin):
    list_display = (
        'char_level', 'stage_id', 'func_id', 'socket_amount'
    )



class DialogStatementinline(admin.TabularInline):
    model = DialogStatement
    extra = 1

class DialogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'stage_id', 'ground_id', 'start_at'
    )

    inlines = [DialogStatementinline,]

    list_filter = ('stage_id', )


admin.site.register(CharInit, CharInitAdmin)
admin.site.register(ArenaReward, ArenaRewardAdmin)
admin.site.register(Notify, NotifyAdmin)
admin.site.register(FunctionOpen, FunctionOpenAdmin)
admin.site.register(Dialog, DialogAdmin)
