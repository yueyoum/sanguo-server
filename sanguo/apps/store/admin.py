from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.store.models import Store, StoreBuyLog

class StoreResources(resources.ModelResource):
    class Meta:
        model = Store


class StoreAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'tag_id', 'item_tp', 'item',
        'sell_tp', 'original_price', 'sell_price',
        'total_amount', 'limit_amount', 'vip_condition', 'char_level',
    )

    resource_class = StoreResources
    list_filter = ('tag_id', 'item_tp', 'sell_tp',)


class StoreBuyLogAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'char_id', 'tag_id', 'item_tp', 'item', 'sell_tp',
        'sell_price', 'amount', 'buy_time', 'status',
    )


admin.site.register(Store, StoreAdmin)
admin.site.register(StoreBuyLog, StoreBuyLogAdmin)
