import hashlib
import logging
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.catalog.pricing import is_wholesale_customer, product_unit_price
from apps.compare.models import CompareItem
from apps.wishlist.models import WishlistItem

from .models import Category, Product, ProductImage

logger = logging.getLogger(__name__)

_IMAGE_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


def product_image_proxy(request: HttpRequest, pk: int) -> HttpResponse:
    """Fetch and cache external product images under our domain."""
    img = get_object_or_404(ProductImage.objects.only("pk", "image_url", "image"), pk=pk)

    if img.image:
        return HttpResponseRedirect(img.image.url)

    parsed = urlparse(img.image_url)
    allowed = getattr(settings, "IMAGE_PROXY_ALLOWED_HOSTS", set())
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in allowed:
        raise Http404

    cache_key = f"product_image:{pk}:{hashlib.sha256(img.image_url.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        content, content_type = cached
        response = HttpResponse(content, content_type=content_type)
        response["Cache-Control"] = "public, max-age=604800, immutable"
        return response

    try:
        upstream = requests.get(
            img.image_url,
            timeout=15,
            headers={"User-Agent": "DOMOTEH-ImageProxy/1.0"},
        )
        upstream.raise_for_status()
    except requests.RequestException:
        logger.warning("Image proxy failed for ProductImage #%s", pk)
        raise Http404 from None

    content_type = upstream.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    if not content_type.startswith("image/"):
        raise Http404

    content = upstream.content
    cache.set(cache_key, (content, content_type), _IMAGE_CACHE_TTL)

    response = HttpResponse(content, content_type=content_type)
    response["Cache-Control"] = "public, max-age=604800, immutable"
    return response


def homepage(request: HttpRequest) -> HttpResponse:
    new_products = Product.objects.filter(is_available=True).order_by("-created_at")[:20]
    bestsellers = Product.objects.filter(is_available=True, is_bestseller=True)[:20]
    popular = Product.objects.filter(is_available=True).order_by("-updated_at")[:20]

    top_categories = Category.objects.filter(level=0, is_active=True)
    category_sections = []
    for cat in top_categories:
        products = Product.objects.filter(
            category__in=cat.get_descendants(include_self=True),
            is_available=True,
        ).order_by("-created_at")[:5]
        if products:
            category_sections.append({"category": cat, "products": products})

    return render(request, "catalog/home.html", {
        "new_products": new_products,
        "bestsellers": bestsellers,
        "popular": popular,
        "category_sections": category_sections,
    })


def category_detail(request: HttpRequest, slug: str) -> HttpResponse:
    category = get_object_or_404(Category, slug=slug, is_active=True)
    descendants = category.get_descendants(include_self=True)
    products = Product.objects.filter(category__in=descendants, is_available=True)

    sort = request.GET.get("sort", "-created_at")
    allowed_sorts = {
        "price_asc": "retail_price",
        "price_desc": "-retail_price",
        "name": "name",
        "new": "-created_at",
    }
    products = products.order_by(allowed_sorts.get(sort, "-created_at"))

    brand = request.GET.get("brand")
    if brand:
        products = products.filter(brand=brand)

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        products = products.filter(retail_price__gte=min_price)
    if max_price:
        products = products.filter(retail_price__lte=max_price)

    paginator = Paginator(products, 24)
    page = paginator.get_page(request.GET.get("page"))

    brands = (
        Product.objects.filter(category__in=descendants, is_available=True)
        .exclude(brand="")
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

    template = "catalog/partials/product_grid.html" if request.htmx else "catalog/category.html"
    return render(request, template, {
        "category": category,
        "page_obj": page,
        "brands": brands,
        "current_sort": sort,
        "current_brand": brand or "",
    })


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related(
            "images", "params", "wholesale_prices", "reviews"
        ),
        slug=slug,
    )
    is_wholesale = is_wholesale_customer(request.user)
    wholesale = product.get_wholesale_price()
    customer_unit_price = product_unit_price(product, request.user, 1)

    related = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(pk=product.pk)[:15]

    in_wishlist = (
        request.user.is_authenticated
        and WishlistItem.objects.filter(user=request.user, product=product).exists()
    )

    session_key = request.session.session_key
    if request.user.is_authenticated:
        in_compare = CompareItem.objects.filter(user=request.user, product=product).exists()
    elif session_key:
        in_compare = CompareItem.objects.filter(session_key=session_key, user=None, product=product).exists()
    else:
        in_compare = False

    return render(request, "catalog/product.html", {
        "product": product,
        "wholesale": wholesale,
        "is_wholesale": is_wholesale,
        "customer_unit_price": customer_unit_price,
        "related_products": related,
        "in_wishlist": in_wishlist,
        "in_compare": in_compare,
    })


def search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(brand__icontains=query),
            is_available=True,
        )
    paginator = Paginator(products, 24)
    page = paginator.get_page(request.GET.get("page"))

    template = "catalog/partials/product_grid.html" if request.htmx else "catalog/search.html"
    return render(request, template, {"page_obj": page, "query": query})
