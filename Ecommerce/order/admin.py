from django.contrib import admin

from . import models


class OrderItemInline(admin.TabularInline):
    """Order lines shown inside the order page; they are a snapshot, so read-only."""

    model = models.OrderItem
    fields = ['product', 'quantity', 'unit_price', 'total_price']
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'total_price']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email']
    list_select_related = ['user']

    # Only the status can change; everything else is a record of the purchase.
    fields = ['user', 'status', 'created_at', 'total_price']
    readonly_fields = ['user', 'created_at', 'total_price']
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        # Orders are created by checkout, not by hand.
        return False