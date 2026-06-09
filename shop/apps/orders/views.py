import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.cart.services import clear_cart, get_cart_items
from apps.catalog.pricing import cart_line_subtotal, product_unit_price
from apps.payments.services import create_monobank_invoice

from .forms import CheckoutForm
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


def checkout(request: HttpRequest) -> HttpResponse:
    cart_items = get_cart_items(request)
    if not cart_items:
        return redirect("cart:detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total = sum(
                cart_line_subtotal(i.product, request.user, i.quantity) for i in cart_items
            )
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    sku=item.product.sku,
                    quantity=item.quantity,
                    price=product_unit_price(item.product, request.user, item.quantity),
                )
            clear_cart(request)

            if order.payment_method == Order.PaymentMethod.MONOBANK:
                redirect_url = request.build_absolute_uri(
                    reverse("orders:success", kwargs={"pk": order.pk})
                )
                webhook_url = request.build_absolute_uri(
                    reverse("payments:monobank_callback")
                )
                page_url = create_monobank_invoice(order, redirect_url, webhook_url)
                if page_url:
                    return redirect(page_url)

                # MonoBank API unavailable — order saved, manager will follow up
                logger.error("MonoBank invoice creation failed for order #%s", order.pk)
                order.status = Order.Status.CONFIRMED
                order.save(update_fields=["status"])

            return redirect("orders:success", pk=order.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "phone": getattr(request.user, "phone", ""),
            }
        form = CheckoutForm(initial=initial)

    total = sum(
        cart_line_subtotal(i.product, request.user, i.quantity) for i in cart_items
    )
    return render(request, "orders/checkout.html", {
        "form": form, "cart_items": cart_items, "cart_total": total,
    })


def order_success(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk)
    payment = (
        order.payments
        .filter(provider="monobank")
        .order_by("-created_at")
        .first()
    )
    return render(request, "orders/success.html", {
        "order": order,
        "payment": payment,
    })


def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/detail.html", {"order": order})


@login_required
def order_history(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/history.html", {"orders": orders})
