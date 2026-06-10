from decimal import Decimal, ROUND_HALF_UP

from django.contrib import admin, messages
from django.db import models, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from django_ckeditor_5.widgets import CKEditor5Widget
from mptt.admin import DraggableMPTTAdmin
from unfold.admin import ModelAdmin, TabularInline

from .forms import BulkPriceForm
from .models import Category, Product, ProductImage, ProductParam, WholesalePrice


def _apply_rounding(value: Decimal, rounding: str) -> Decimal:
    if rounding == "none":
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    step = Decimal(rounding)
    return (value / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step


def _calc_new_price(price: Decimal, change_type: str, direction: str, value: Decimal, rounding: str) -> Decimal:
    if change_type == "percent":
        if direction == "increase":
            new = price * (1 + value / Decimal("100"))
        else:
            new = price * (1 - value / Decimal("100"))
    else:
        if direction == "increase":
            new = price + value
        else:
            new = price - value
    new = max(new, Decimal("0.01"))
    return _apply_rounding(new, rounding)


@admin.register(Category)
class CategoryAdmin(ModelAdmin, DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ("get_image_preview", "image", "sort_order")
    readonly_fields = ("get_image_preview",)

    @admin.display(description="Прев'ю")
    def get_image_preview(self, obj: ProductImage) -> str:
        if not obj.pk:
            return "—"
        src = obj.url
        if not src:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:60px;max-width:80px;object-fit:contain;border-radius:4px">',
            src,
        )


class ProductParamInline(TabularInline):
    model = ProductParam
    extra = 0


class WholesalePriceInline(TabularInline):
    model = WholesalePrice
    extra = 0


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        "get_image_preview", "name", "sku", "retail_price",
        "is_available", "is_new", "is_bestseller", "category",
    )
    list_filter = ("is_available", "is_new", "is_bestseller", "category")
    search_fields = ("name", "sku", "offer_id")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductParamInline, WholesalePriceInline]
    list_editable = ("is_available", "is_new", "is_bestseller")
    raw_id_fields = ("category",)
    readonly_fields = ("get_image_preview",)
    formfield_overrides = {
        models.TextField: {"widget": CKEditor5Widget(config_name="default")},
    }
    actions = ["action_bulk_price"]

    @admin.display(description="Фото")
    def get_image_preview(self, obj: Product) -> str:
        first = obj.images.first()
        if not first:
            return "—"
        src = first.url
        if not src:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:60px;max-width:80px;object-fit:contain;border-radius:4px">',
            src,
        )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "bulk-price/",
                self.admin_site.admin_view(self.bulk_price_view),
                name="catalog_product_bulk_price",
            ),
        ]
        return custom + urls

    @admin.action(description="💰 Змінити ціни (масово)")
    def action_bulk_price(self, request, queryset):
        ids = queryset.values_list("pk", flat=True)
        id_str = ",".join(str(i) for i in ids)
        url = reverse("admin:catalog_product_bulk_price")
        return HttpResponseRedirect(f"{url}?ids={id_str}")

    def bulk_price_view(self, request):
        ids_param = request.GET.get("ids") or request.POST.get("ids", "")
        if ids_param:
            try:
                id_list = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
            except ValueError:
                id_list = []
            queryset = Product.objects.filter(pk__in=id_list)
            scope_label = f"Вибрані товари ({len(id_list)} шт.)"
        else:
            queryset = Product.objects.all()
            scope_label = f"Усі товари ({Product.objects.count()} шт.)"

        if request.method == "POST":
            form = BulkPriceForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                change_type = cd["change_type"]
                direction = cd["direction"]
                value = cd["value"]
                rounding = cd["rounding"] or "none"
                apply_wholesale = cd["apply_to_wholesale"]
                apply_old_price = cd["apply_to_old_price"]

                updated_retail = 0
                updated_wholesale = 0

                with transaction.atomic():
                    products = list(queryset.only("pk", "retail_price", "old_price"))
                    for product in products:
                        product.retail_price = _calc_new_price(
                            product.retail_price, change_type, direction, value, rounding
                        )
                        if apply_old_price and product.old_price:
                            product.old_price = _calc_new_price(
                                product.old_price, change_type, direction, value, rounding
                            )
                    update_fields = ["retail_price"]
                    if apply_old_price:
                        update_fields.append("old_price")

                    Product.objects.bulk_update(products, update_fields, batch_size=500)
                    updated_retail = len(products)

                    if apply_wholesale:
                        wp_list = list(
                            WholesalePrice.objects.filter(product__in=queryset).only("pk", "price")
                        )
                        for wp in wp_list:
                            wp.price = _calc_new_price(
                                wp.price, change_type, direction, value, rounding
                            )
                        WholesalePrice.objects.bulk_update(wp_list, ["price"], batch_size=500)
                        updated_wholesale = len(wp_list)

                direction_label = "підняті" if direction == "increase" else "знижені"
                type_label = f"{value}%" if change_type == "percent" else f"{value} грн"
                msg = (
                    f"Ціни {direction_label} на {type_label}. "
                    f"Оновлено роздрібних: {updated_retail}"
                )
                if apply_wholesale:
                    msg += f", гуртових позицій: {updated_wholesale}"
                self.message_user(request, msg, messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:catalog_product_changelist"))
        else:
            form = BulkPriceForm()

        preview = queryset.order_by("name").values("pk", "name", "sku", "retail_price")[:20]

        context = {
            **self.admin_site.each_context(request),
            "title": "Масова зміна цін",
            "form": form,
            "preview": preview,
            "scope_label": scope_label,
            "ids_param": ids_param,
            "total_count": queryset.count(),
            "opts": self.model._meta,
        }
        return render(request, "admin/catalog/product/bulk_price_action.html", context)
