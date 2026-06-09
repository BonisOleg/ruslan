from apps.catalog.pricing import cart_line_subtotal
from .services import get_cart_items


def cart_summary(request):
    items = get_cart_items(request)
    total_qty = sum(i.quantity for i in items)
    total_price = sum(
        cart_line_subtotal(i.product, request.user, i.quantity) for i in items
    )
    return {
        "cart_items_count": total_qty,
        "cart_total": total_price,
    }
