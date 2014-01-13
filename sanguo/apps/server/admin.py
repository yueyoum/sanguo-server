from django.contrib import admin

from apps.server.models import Server, ServerStatus

class ServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'create_at', 'active',
    'CharAmount', 'LoginTimes',
    'PayPlayersAmount', 'PayTotal',
    'PVETimes', 'PVPTimes'
    )

    exclude = ('create_at', )

    def _get_status(self, obj):
        s = getattr(self, '_server_status', None)
        if s is None:
            s = ServerStatus.objects.get(server_id=obj.id)
            self._server_status = s
        return s

    def CharAmount(self, obj):
        s = self._get_status(obj)
        return s.char_amount

    def LoginTimes(self, obj):
        s = self._get_status(obj)
        return s.login_times

    def PayPlayersAmount(self, obj):
        s = self._get_status(obj)
        return s.pay_players_amount

    def PayTotal(self, obj):
        s = self._get_status(obj)
        return s.pay_total

    def PVETimes(self, obj):
        s = self._get_status(obj)
        return s.pve_times

    def PVPTimes(self, obj):
        s = self._get_status(obj)
        return s.pvp_times

admin.site.register(Server, ServerAdmin)
