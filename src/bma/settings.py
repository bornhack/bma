"""Django settings for bma project."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from pathlib import Path

import django_stubs_ext

from utils.ninjafix import monkeypatch_ninja_uuid_converter

from .environment_settings import *  # noqa: F403

# get BMA_VERSION from package registry
try:
    BMA_VERSION = version("bma")
except PackageNotFoundError:
    BMA_VERSION = "0.0.0"

# intialise django_stubs_ext
django_stubs_ext.monkeypatch()

# https://github.com/vitalik/django-ninja/issues/1266
monkeypatch_ninja_uuid_converter()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    "django.contrib.humanize",
    # deps
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_bootstrap5",
    "fontawesomefree",
    "polymorphic",
    "ninja",
    "django_htmx",
    "oauth2_provider",
    "guardian",
    "corsheaders",
    "django_filters",
    "django_tables2",
    "pictures",
    # bma apps
    "bornhack_allauth_provider",
    "users",
    "utils",
    "files",
    "images",
    "videos",
    "audios",
    "documents",
    "frontpage",
    "albums",
    "widgets",
    "tags",
    "hitcounter",
    "jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
]

ROOT_URLCONF = "bma.urls"

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
                "django.template.context_processors.media",
                "utils.context_processors.bma_version",
            ],
            "builtins": [
                "pictures.templatetags.pictures",
                "utils.templatetags.bma_utils",
            ],
        },
    },
]

WSGI_APPLICATION = "bma.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Copenhagen"

USE_I18N = True

USE_L10N = False

USE_TZ = True

SHORT_DATE_FORMAT = "Ymd"
DATE_FORMAT = "l, M jS, Y"
DATETIME_FORMAT = "l, M jS, Y, H:i (e)"
TIME_FORMAT = "H:i"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATICFILES_DIRS = [BASE_DIR / "static_src"]  # find static files below here
STATIC_ROOT = BASE_DIR / "static"  # collect all static files here
STATIC_URL = "static/"  # serve the static files here

MEDIA_URL = "media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Allauth
# avoid socialaccount_state bug / session cookie name conflicts
SESSION_COOKIE_NAME = "bma_sessionid"
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
AUTH_USER_MODEL = "users.User"
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USER_MODEL_EMAIL_FIELD = None
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_ADAPTER = "users.adapter.NoNewUsersAccountAdapter"
SOCIALACCOUNT_ADAPTER = "bornhack_allauth_provider.adapters.BornHackSocialAccountAdapter"
SOCIALACCOUNT_ONLY = True

# taggit
TAGGIT_CASE_INSENSITIVE = True

X_FRAME_OPTIONS = "SAMEORIGIN"

# https://docs.djangoproject.com/en/4.1/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "formatters": {
        "syslog": {"format": "%(levelname)s %(name)s.%(funcName)s(): %(message)s"},
        "console": {
            "format": "[%(asctime)s] %(name)s.%(funcName)s() %(levelname)s %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,  # noqa: F405
            "propagate": False,
        },
        "bma": {
            "handlers": ["console"],
            "level": BMA_LOG_LEVEL,  # noqa: F405
            "propagate": False,
        },
    },
}

GUARDIAN_GET_CONTENT_TYPE = "polymorphic.contrib.guardian.get_polymorphic_base_content_type"

# save csrf tokens in session instead of using double cookie to ease api scripting
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = not DEBUG  # noqa: F405
SESSION_COOKIE_SECURE = not DEBUG  # noqa: F405

if DEBUG_TOOLBAR:  # noqa: F405
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"

BOOTSTRAP5 = {
    "css_url": {
        "url": "/static/css/vendor/bootstrap-v5.3.3.min.css",
        "integrity": "sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH",
        "crossorigin": "anonymous",
    },
    "javascript_url": {
        "url": "/static/js/vendor/bootstrap-v5.3.3.bundle.min.js",
        "integrity": "sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz",
        "crossorigin": "anonymous",
    },
}

HITCOUNT_HITCOUNT_MODEL = "utils.HitCount"

PICTURES = {
    "BREAKPOINTS": {
        "xs": 0,
        "sm": 576,
        "md": 768,
        "lg": 992,
        "xl": 1200,
        "xxl": 1400,
    },
    "GRID_COLUMNS": 12,
    "CONTAINER_WIDTH": 4000,
    "FILE_TYPES": ["WEBP"],
    "PIXEL_DENSITIES": [1, 2],
    "USE_PLACEHOLDERS": False,
    "PROCESSOR": "images.picture_processor.dummy_processor",
}
