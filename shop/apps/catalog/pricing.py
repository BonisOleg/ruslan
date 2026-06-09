from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.models import AnonymousUser

from apps.catalog.models import Product


def is_wholesale_customer(user) -> bool:
    return bool(
        user
        and not isinstance(user, AnonymousUser)
        and user.is_authenticated
        and getattr(user, "is_wholesale", False)
    )


def product_unit_price(product: Product, user, quantity: int = 1) -> Decimal:
    return product.get_price_for_quantity(
        quantity,
        is_wholesale_user=is_wholesale_customer(user),
    )


def cart_line_subtotal(product: Product, user, quantity: int) -> Decimal:
    unit = product_unit_price(product, user, quantity)
    return unit * quantity
