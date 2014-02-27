from django.contrib import admin

from apps.mail.models import Mail

class MailAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'content',
        'gold', 'sycee', 'exp', 'official_exp', 'heros',
        'equipments', 'gems', 'stuffs',
        'create_at', 'send_at',
        'send_type', 'send_to',
        'send_lock', 'send_done',
    )

    fieldsets = (
        ('', {
            'fields': ('name', 'content', 'send_at', 'send_type', 'send_to'),
        }),
        ('Attachment', {
            'classes': ('grp-collapse', 'grp-closed'),
            'fields': ('gold', 'sycee', 'exp', 'official_exp', 'heros', 'equipments', 'gems', 'stuffs')
        }),
    )

admin.site.register(Mail, MailAdmin)