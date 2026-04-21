from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

ENVIRONMENT = config("ENVIRONMENT", default="development")
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"


def config_bool(name, default=False):
    value = config(name, default=None)
    if value is None or value == "":
        return default

    normalized_value = str(value).strip().lower()
    if normalized_value in {"1", "true", "t", "yes", "y", "on", "development", "dev"}:
        return True
    if normalized_value in {
        "0",
        "false",
        "f",
        "no",
        "n",
        "off",
        "production",
        "prod",
        "release",
    }:
        return False

    raise ImproperlyConfigured(f"{name} must be a boolean value.")


SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-in-production")

DEBUG = config_bool("DEBUG", default=IS_DEVELOPMENT)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="*" if IS_DEVELOPMENT else "",
    cast=Csv(),
)

if IS_PRODUCTION:
    if DEBUG:
        raise ImproperlyConfigured("DEBUG=False is required when ENVIRONMENT=production.")
    if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "Set explicit ALLOWED_HOSTS when ENVIRONMENT=production."
        )

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "corsheaders",
    "transactions",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=config("DB_CONN_MAX_AGE", default=0 if DEBUG else 600, cast=int),
        ssl_require=config_bool("DB_SSL_REQUIRE", default=IS_PRODUCTION),
    )
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOWED_ORIGIN_REGEXES = config(
    "CORS_ALLOWED_ORIGIN_REGEXES",
    default="",
    cast=Csv(),
)
CORS_ALLOW_ALL_ORIGINS = config_bool(
    "CORS_ALLOW_ALL_ORIGINS",
    default=IS_DEVELOPMENT,
)

if IS_PRODUCTION and CORS_ALLOW_ALL_ORIGINS:
    raise ImproperlyConfigured(
        "CORS_ALLOW_ALL_ORIGINS=False is required when ENVIRONMENT=production."
    )

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
