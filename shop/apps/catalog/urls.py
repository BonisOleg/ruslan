from django.urls import path, register_converter

from . import views


class UnicodeSlugConverter:
    regex = r"[-\w]+"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


register_converter(UnicodeSlugConverter, "uslug")

app_name = "catalog"

urlpatterns = [
    path("", views.homepage, name="home"),
    path("search/", views.search, name="search"),
    path("image/<int:pk>/", views.product_image_proxy, name="image_proxy"),
    path("category/<uslug:slug>/", views.category_detail, name="category"),
    path("product/<uslug:slug>/", views.product_detail, name="product"),
]
