from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.official.models import Official

class OfficialResources(resources.ModelResource):
    class Meta:
        model = Official

class OfficialAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'name', 'gold', #'stuffs',
    )

    resource_class = OfficialResources

admin.site.register(Official, OfficialAdmin)

