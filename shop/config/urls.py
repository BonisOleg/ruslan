from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "Адміністрування магазину"
admin.site.site_title = "Магазин"
admin.site.index_title = "Панель керування"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("", include("apps.catalog.urls")),
    path("cart/", include("apps.cart.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),
    path("shipping/", include("apps.shipping.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
    path("compare/", include("apps.compare.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("blog/", include("apps.blog.urls")),
    path("pages/", include("apps.pages.urls")),
]

# Serve media locally when no cloud storage is configured (dev + Render without Cloudinary)
_using_cloud = bool(getattr(settings, "CLOUDINARY_URL", ""))
if settings.DEBUG or not _using_cloud:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
