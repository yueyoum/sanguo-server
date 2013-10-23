from django.contrib import admin
from models import Character, CharHero
from apps.hero.models import Hero


class CharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_id', 'server_id', 'name',
            'gold', 'gem', 'level', 'honor',
            )

    list_filter = ('account_id', 'server_id', )

class CharHeroAdmin(admin.ModelAdmin):
    list_display = ('id', 'char', 'hero_id',
            'level', 'exp',
            )

    list_filter = ('char',)



admin.site.register(Character, CharacterAdmin)
admin.site.register(CharHero, CharHeroAdmin)

