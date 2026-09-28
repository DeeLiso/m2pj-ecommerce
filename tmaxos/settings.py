"""
Django settings for the T-MAX-OS E-Commerce website.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "tmaxos-dev-secret-key-change-me-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "store.apps.StoreConfig",
    "accounts.apps.AccountsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tmaxos.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.cart_count",
                "store.context_processors.engagement",
                "store.context_processors.support_links",
            ],
        },
    },
]

WSGI_APPLICATION = "tmaxos.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Yangon"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "store:home"
LOGOUT_REDIRECT_URL = "store:home"

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ------------------------------------------------------------------
# Payment configuration (Test mode)
# Set these in your environment when going live. When STRIPE_SECRET_KEY
# is enabled the checkout will create real Stripe PaymentIntents.
# ------------------------------------------------------------------
PAYMENT_METHOD = os.environ.get("PAYMENT_METHOD", "demo")  # "demo" | "stripe" | "cod"
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

# Wallet payment accounts (shown to customers for KBZ Pay / Wave Money transfers)
KBZ_PAY_NUMBER = os.environ.get("KBZ_PAY_NUMBER", "09 123 456 789")
WAVE_PAY_NUMBER = os.environ.get("WAVE_PAY_NUMBER", "09 987 654 321")

# Support / chat channels (shown in the floating chat widget)
VIBER_LINK = os.environ.get("VIBER_LINK", "viber://chat?number=%2B959123456789")
FACEBOOK_MESSENGER_URL = os.environ.get("FACEBOOK_MESSENGER_URL", "https://m.me/tmaxos.shop")
WHATSAPP_LINK = os.environ.get("WHATSAPP_LINK", "https://wa.me/959123456789")
TELEGRAM_URL = os.environ.get("TELEGRAM_URL", "https://t.me/tmaxos_support")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"