from __future__ import annotations

from django.db.models import QuerySet
from django.http import HttpRequest

from .models import CartItem


def _ensure_session(request: HttpRequest) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_cart_items(request: HttpRequest) -> QuerySet[CartItem]:
    qs = CartItem.objects.select_related("product").prefetch_related(
        "product__images", "product__wholesale_prices"
    )
    if request.user.is_authenticated:
        return qs.filter(user=request.user)
    session_key = request.session.session_key
    if not session_key:
        return CartItem.objects.none()
    return qs.filter(session_key=session_key)


def add_to_cart(request: HttpRequest, product_id: int, quantity: int = 1) -> CartItem:
    if request.user.is_authenticated:
        item, created = CartItem.objects.get_or_create(
            user=request.user, product_id=product_id,
            defaults={"quantity": quantity},
        )
    else:
        session_key = _ensure_session(request)
        item, created = CartItem.objects.get_or_create(
            session_key=session_key, product_id=product_id, user=None,
            defaults={"quantity": quantity},
        )
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity", "updated_at"])
    return item


def update_quantity(request: HttpRequest, item_id: int, quantity: int) -> CartItem | None:
    qs = get_cart_items(request).filter(id=item_id)
    item = qs.first()
    if not item:
        return None
    if quantity <= 0:
        item.delete()
        return None
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item


def remove_from_cart(request: HttpRequest, item_id: int) -> bool:
    deleted, _ = get_cart_items(request).filter(id=item_id).delete()
    return deleted > 0


def merge_cart_on_login(request: HttpRequest) -> None:
    """Move anonymous cart items to the authenticated user."""
    session_key = request.session.session_key
    if not session_key or not request.user.is_authenticated:
        return
    anon_items = CartItem.objects.filter(session_key=session_key, user=None)
    for item in anon_items:
        existing = CartItem.objects.filter(user=request.user, product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save(update_fields=["quantity", "updated_at"])
            item.delete()
        else:
            item.user = request.user
            item.session_key = ""
            item.save(update_fields=["user", "session_key", "updated_at"])


def clear_cart(request: HttpRequest) -> None:
    get_cart_items(request).delete()
