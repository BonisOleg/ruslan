from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("SECRET_KEY", default="change-me-in-production")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    # Third-party
    "mptt",
    "django_htmx",
    "cloudinary_storage",
    "cloudinary",
    "django_ckeditor_5",
    # Project apps
    "apps.accounts",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.wishlist",
    "apps.compare",
    "apps.reviews",
    "apps.pages",
    "apps.blog",
    "apps.shipping",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.accounts.context_processors.wholesale_customer",
                "apps.catalog.context_processors.categories_menu",
                "apps.cart.context_processors.cart_summary",
                "apps.pages.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

CSV_DATA_DIR = BASE_DIR.parent / "output"

# Serve external product images through our domain (avoids hotlink blocks)
USE_IMAGE_PROXY = env.bool("USE_IMAGE_PROXY", default=False)
IMAGE_PROXY_ALLOWED_HOSTS = {"lmm.in.ua", "www.lmm.in.ua"}

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": {
            "items": [
                "heading", "|",
                "bold", "italic", "underline", "strikethrough", "|",
                "link", "bulletedList", "numberedList", "blockQuote", "|",
                "imageUpload", "mediaEmbed", "|",
                "insertTable", "horizontalLine", "|",
                "undo", "redo",
            ],
        },
        "image": {
            "toolbar": [
                "imageStyle:inline",
                "imageStyle:block",
                "imageStyle:side",
                "|",
                "toggleImageCaption",
                "imageTextAlternative",
            ],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"],
        },
        "height": "400px",
        "width": "100%",
    },
}

UNFOLD = {
    "SITE_TITLE": "DOMOTEH Адмінка",
    "SITE_HEADER": "DOMOTEH — Управління магазином",
    "SITE_URL": "/",
    "SITE_SYMBOL": "storefront",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "LOGO": "/static/images/logo.png",
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Каталог",
                "icon": "inventory_2",
                "items": [
                    {"title": "Категорії", "icon": "category", "link": "/admin/catalog/category/"},
                    {"title": "Товари", "icon": "shopping_bag", "link": "/admin/catalog/product/"},
                ],
            },
            {
                "title": "Замовлення",
                "icon": "receipt_long",
                "items": [
                    {"title": "Замовлення", "icon": "orders", "link": "/admin/orders/order/"},
                    {"title": "Платежі", "icon": "payments", "link": "/admin/payments/payment/"},
                ],
            },
            {
                "title": "Клієнти",
                "icon": "group",
                "items": [
                    {"title": "Користувачі", "icon": "person", "link": "/admin/accounts/user/"},
                    {"title": "Відгуки", "icon": "star", "link": "/admin/reviews/review/"},
                    {"title": "Питання", "icon": "help", "link": "/admin/reviews/question/"},
                    {"title": "Підписники", "icon": "mail", "link": "/admin/pages/newslettersubscriber/"},
                ],
            },
            {
                "title": "Контент",
                "icon": "article",
                "items": [
                    {"title": "Статичні сторінки", "icon": "description", "link": "/admin/pages/staticpage/"},
                    {"title": "Блог", "icon": "feed", "link": "/admin/blog/blogpost/"},
                ],
            },
            {
                "title": "Налаштування",
                "icon": "settings",
                "items": [
                    {"title": "Налаштування сайту", "icon": "tune", "link": "/admin/pages/sitesettings/1/change/"},
                ],
            },
        ],
    },
}

# MonoBank Acquiring
MONOBANK_TOKEN = env("MONOBANK_TOKEN", default="")
MONOBANK_API_BASE = "https://api.monobank.ua"

# Nova Poshta
NOVA_POSHTA_API_KEY = env("NOVA_POSHTA_API_KEY", default="")
# Sender configuration — fill in the merchant cabinet values
NOVA_POSHTA_SENDER_REF = env("NOVA_POSHTA_SENDER_REF", default="")
NOVA_POSHTA_CONTACT_SENDER_REF = env("NOVA_POSHTA_CONTACT_SENDER_REF", default="")
NOVA_POSHTA_SENDER_CITY_REF = env("NOVA_POSHTA_SENDER_CITY_REF", default="")
NOVA_POSHTA_SENDER_WAREHOUSE_REF = env("NOVA_POSHTA_SENDER_WAREHOUSE_REF", default="")
NOVA_POSHTA_SENDER_PHONE = env("NOVA_POSHTA_SENDER_PHONE", default="")
