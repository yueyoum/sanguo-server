from django.contrib import admin
from models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'passwd', 'device_token', 'last_login')


admin.site.register(User, UserAdmin)

