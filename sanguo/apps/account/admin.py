# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/13/14'

from django.contrib import admin
from apps.account.models import Account

class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email', 'device_token', 'register_at', 'last_login', 'last_server_id', 'all_server_ids',
        'login_times', 'active'
    )

    fields = (
        'email', 'active'
    )

    ordering = ('-last_login', )

    def has_add_permission(self, request):
        return False

admin.site.register(Account, AccountAdmin)
