from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True, allow_unicode=True)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Батьківська категорія",
    )
    image = models.ImageField("Зображення", upload_to="categories/", blank=True)
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.IntegerField("Порядок", default=0)
    original_id = models.CharField("ID з імпорту", max_length=50, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ["sort_order", "name"]

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:category", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            if Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{self.slug}-{self.original_id or self.pk or 'x'}"
        super().save(*args, **kwargs)


class Product(models.Model):
    offer_id = models.CharField("ID пропозиції", max_length=50, unique=True, db_index=True)
    sku = models.CharField("Артикул (SKU)", max_length=100, blank=True, db_index=True)
    name = models.CharField("Назва", max_length=500)
    slug = models.SlugField("Slug", max_length=500, unique=True, allow_unicode=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Категорія",
    )
    brand = models.CharField("Бренд", max_length=255, blank=True, db_index=True)
    description = models.TextField("Опис", blank=True)
    retail_price = models.DecimalField("Роздрібна ціна", max_digits=12, decimal_places=2, default=0)
    old_price = models.DecimalField("Стара ціна", max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField("Валюта", max_length=5, default="UAH")
    is_available = models.BooleanField("В наявності", default=True)
    is_new = models.BooleanField("Новинка", default=False)
    is_bestseller = models.BooleanField("Хіт продажів", default=False)
    box_quantity = models.PositiveIntegerField("Кількість в ящику", default=0)
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_available", "-created_at"]),
            models.Index(fields=["category", "is_available"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:product", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name[:200], allow_unicode=True) or "product"
            self.slug = base
            if Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{self.offer_id}"
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        return self.images.first()

    @property
    def has_discount(self) -> bool:
        return bool(self.old_price and self.old_price > self.retail_price)

    @property
    def discount_percent(self) -> int:
        if not self.has_discount:
            return 0
        return int(100 - (self.retail_price / self.old_price * 100))

    def get_wholesale_price(self) -> "WholesalePrice | None":
        return self.wholesale_prices.order_by("min_quantity").first()

    def get_price_for_quantity(self, quantity: int, is_wholesale_user: bool = False) -> Decimal:
        if not is_wholesale_user:
            return self.retail_price
        wp = self.wholesale_prices.filter(min_quantity__lte=quantity).order_by("-min_quantity").first()
        return wp.price if wp else self.retail_price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField("URL зображення", max_length=500)
    image = models.ImageField("Локальне зображення", upload_to="products/", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Зображення товару"
        verbose_name_plural = "Зображення товарів"
        ordering = ["sort_order"]

    def __str__(self) -> str:
        return f"{self.product.name} — зображення {self.sort_order}"

    @property
    def url(self) -> str:
        if self.image:
            return self.image.url
        from django.conf import settings

        if getattr(settings, "USE_IMAGE_PROXY", False) and self.pk:
            from django.urls import reverse

            return reverse("catalog:image_proxy", kwargs={"pk": self.pk})
        return self.image_url


class ProductParam(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="params")
    name = models.CharField("Параметр", max_length=255)
    value = models.CharField("Значення", max_length=500)

    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


class WholesalePrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wholesale_prices")
    min_quantity = models.PositiveIntegerField("Мін. кількість")
    price = models.DecimalField("Гуртова ціна", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Гуртова ціна"
        verbose_name_plural = "Гуртові ціни"
        ordering = ["min_quantity"]
        unique_together = [("product", "min_quantity")]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.min_quantity}+ шт. = {self.price} грн"
