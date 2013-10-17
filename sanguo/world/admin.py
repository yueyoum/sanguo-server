from django.contrib import admin
from models import Server


class ServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'max_player_count', 'active', 'create_time')
    exclude = ('create_time',)



admin.site.register(Server, ServerAdmin)
