from django.contrib import admin

from apps.config.models import CharInit

class CharInitAdmin(admin.ModelAdmin):
    list_display = (
        'gold', 'sycee',
        'heros', 'gems', 'stuffs'
    )

admin.site.register(CharInit, CharInitAdmin)

