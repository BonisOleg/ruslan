from .base import *  # noqa: F401, F403

DEBUG = False
USE_IMAGE_PROXY = True

DATABASES = {
    "default": env.db("DATABASE_URL"),  # noqa: F405
}

REDIS_URL = env("REDIS_URL", default="")  # noqa: F405
if REDIS_URL:
    CACHES = {
        "default": env.cache("REDIS_URL"),  # noqa: F405
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CLOUDINARY_URL = env("CLOUDINARY_URL", default="")  # noqa: F405
if CLOUDINARY_URL:
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="shop@lmm.in.ua")  # noqa: F405

# Render.com injects RENDER_EXTERNAL_URL automatically (e.g. https://lmm-shop.onrender.com)
_render_url = env("RENDER_EXTERNAL_URL", default="").rstrip("/")  # noqa: F405
if _render_url:
    CSRF_TRUSTED_ORIGINS = list(CSRF_TRUSTED_ORIGINS)
    if _render_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_url)
    _render_host = _render_url.removeprefix("https://").removeprefix("http://").split("/")[0]
    if _render_host and _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS = list(ALLOWED_HOSTS)
        ALLOWED_HOSTS.append(_render_host)

for origin in env.list("EXTRA_CSRF_ORIGINS", default=[]):  # noqa: F405
    origin = origin.rstrip("/")
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

for host in env.list("EXTRA_ALLOWED_HOSTS", default=[]):  # noqa: F405
    host = host.strip()
    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)
