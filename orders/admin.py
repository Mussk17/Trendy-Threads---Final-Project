from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_id', 'variant_id', 'size', 'color', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['email', 'stripe_payment_intent_id', 'stripe_session_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_session_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
