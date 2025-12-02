import sys
from datetime import timedelta

from django.core.files.storage import FileSystemStorage

import environ

ROOT_DIR = environ.Path(__file__) - 3
APPS_DIR = ROOT_DIR.path("apps")

env = environ.Env()

ENVIRONMENT = env("ENVIRONMENT")

env.read_env(str(ROOT_DIR.path(".env")))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT_DIR("apps"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "adrf",
    "drf_spectacular",
]

LOCAL_APPS = [
    "accounts",
    "tradings",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "easy_health_check.middleware.HealthCheckMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(ROOT_DIR)],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


SITE_ID = 1
# # DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="psql://postgres_user:postgres_password@postgres:5432/app_db",
    )
}

# DEFAULT AUTO FIELD
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# # PASSWORD VALIDATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa
    },
]


# # INTERNATIONALIZATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = False


# # STATIC
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR("staticfiles"))
STATIC_URL = "/static/"


STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# # DJANGO REST FRAMEWORK
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.paginators.LitePagination",
    "PAGE_SIZE": 20,
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# # AWS S3 CONFIGS
# ------------------------------------------------------------------------------

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="")
AWS_REGION_NAME = env("AWS_DEFAULT_REGION", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_DEFAULT_REGION = env("AWS_DEFAULT_REGION", default="")

# # LLM MODELS
# -------------------------------------------------------------------------------
OPENAI_API_KEY = env.str("OPENAI_API_KEY", default="")

# # STORAGE
# ------------------------------------------------------------------------------
STORAGE_SYSTEM = FileSystemStorage()

# # Athenticacion JWT
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME", default=1440)),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=env.int("REFRESH_TOKEN_LIFETIME", default=86400)),
    "ACCESS_TOKEN_COOKIE": "access",
    "REFRESH_TOKEN_COOKIE": "refresh",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_COOKIE_SAMESITE": "Lax",
    "ROTATE_REFRESH_TOKENS": env.bool("ROTATE_REFRESH_TOKENS", default=False),
    "BLACKLIST_AFTER_ROTATION": env.bool("BLACKLIST_AFTER_ROTATION", default=False),
}


# # CORS
# ------------------------------------------------------------------------------
CORS_URLS_REGEX = r"^/*/.*"
CORS_ORIGIN_WHITELIST = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    "Access-Control-Allow-Origin",
    "Access-Token",
    "Authorization",
    "Content-Type",
    "Content-Description",
    "X-CSRFToken",
    "x-authority",
    "Refresh-Token",
    "User-Agent",
    "Api-Token",
)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# # REDIS
# ------------------------------------------------------------------------------
REDIS_URL = env.str("REDIS_URL", default="redis://redis:6379/0")


# # MIDDLEWARE  # https://pypi.org/project/django-easy-health-check/
# ------------------------------------------------------------------------------
DJANGO_EASY_HEALTH_CHECK = {
    "PATH": "/healthcheck/",
    "RETURN_STATUS_CODE": 200,
    "RETURN_BYTE_DATA": "",
    "RETURN_HEADERS": None,
}


# # LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
