from apps.catalog.pricing import is_wholesale_customer


def wholesale_customer(request):
    return {"is_wholesale_customer": is_wholesale_customer(request.user)}
