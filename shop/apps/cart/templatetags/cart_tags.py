from django import template

from apps.catalog.pricing import cart_line_subtotal, product_unit_price

register = template.Library()


@register.filter
def cart_unit_price(item, user):
    return product_unit_price(item.product, user, item.quantity)


@register.filter
def cart_line_total(item, user):
    return cart_line_subtotal(item.product, user, item.quantity)
