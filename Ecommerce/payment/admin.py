from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payments are financial records: they can be viewed but never added, changed or deleted here."""

    list_display = ['transaction_id', 'order', 'amount', 'status', 'card_last4', 'created_at']
    list_filter = ['status', 'created_at']
    # Find a payment by its reference, or by the email of the customer who paid
    search_fields = ['transaction_id', 'order__user__email']
    # Load each payment's order and its user in the same query, not one query per row
    list_select_related = ['order__user']
    readonly_fields = list_display

    def has_add_permission(self, request):
        # Payments only come from the pay endpoint
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False