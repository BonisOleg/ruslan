from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "sku", "quantity", "price")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id", "first_name", "last_name", "phone",
        "status", "status_badge", "total", "payment_method", "delivery_method",
        "tracking_link", "created_at",
    )
    list_filter = ("status", "payment_method", "delivery_method")
    search_fields = ("first_name", "last_name", "phone", "email", "tracking_number")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "updated_at", "tracking_link", "status_badge")
    list_editable = ("status",)

    fieldsets = (
        ("Замовлення", {
            "fields": ("status", "total", "comment"),
        }),
        ("Клієнт", {
            "fields": ("user", "first_name", "last_name", "email", "phone"),
        }),
        ("Доставка", {
            "fields": (
                "delivery_method", "delivery_address",
                "nova_poshta_city", "nova_poshta_city_ref",
                "nova_poshta_warehouse", "nova_poshta_warehouse_ref",
                "tracking_number", "tracking_link",
            ),
        }),
        ("Оплата", {
            "fields": ("payment_method",),
        }),
        ("Службові", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    _STATUS_COLORS = {
        "new": "blue",
        "confirmed": "indigo",
        "processing": "yellow",
        "shipped": "purple",
        "delivered": "green",
        "cancelled": "red",
        "returned": "gray",
    }

    @admin.display(description="Статус")
    def status_badge(self, obj: Order) -> str:
        color = self._STATUS_COLORS.get(obj.status, "gray")
        label = obj.get_status_display()
        return format_html(
            '<span style="'
            'display:inline-block;padding:2px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;'
            'background:var(--color-{}-100,#e0e7ff);color:var(--color-{}-700,#3730a3)">{}</span>',
            color, color, label,
        )

    @admin.display(description="ТТН / Трекінг")
    def tracking_link(self, obj: Order) -> str:
        if not obj.tracking_number:
            return "—"
        url = f"https://novaposhta.ua/tracking/?cargo_number={obj.tracking_number}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            url,
            obj.tracking_number,
        )
