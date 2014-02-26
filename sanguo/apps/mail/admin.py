from django.contrib import admin

from apps.mail.models import Mail

class MailAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'content',
        'gold', 'sycee', 'exp', 'off_exp', 'heros',
        'equips', 'gems', 'stuffs',
        'create_at', 'send_at',
        'send_type', 'send_to',
        'send_done',
    )

    fieldsets = (
        ('', {
            'fields': ('name', 'content', 'send_at', 'send_type', 'send_to'),
        }),
        ('Attachment', {
            'classes': ('grp-collapse', 'grp-closed'),
            'fields': ('gold', 'sycee', 'exp', 'off_exp', 'heros', 'equips', 'gems', 'stuffs')
        }),
    )

admin.site.register(Mail, MailAdmin)