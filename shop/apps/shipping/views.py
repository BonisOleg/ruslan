"""HTMX endpoints for Nova Poshta city & warehouse autocomplete."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .services import get_warehouses, search_cities


def np_cities(request: HttpRequest) -> HttpResponse:
    """Search cities by query string. Returns partial HTML list."""
    query = (
        request.GET.get("q", "").strip()
        or request.GET.get("nova_poshta_city", "").strip()
    )
    cities = search_cities(query) if len(query) >= 2 else []
    return render(request, "shipping/np_city_results.html", {"cities": cities, "query": query})


def np_warehouses(request: HttpRequest) -> HttpResponse:
    """HTMX: get warehouses for a city ref. Returns partial HTML options."""
    city_ref = request.GET.get("city_ref", "").strip()
    query = request.GET.get("q", "").strip()
    warehouses = get_warehouses(city_ref, query) if city_ref else []
    return render(request, "shipping/np_warehouse_options.html", {"warehouses": warehouses})
