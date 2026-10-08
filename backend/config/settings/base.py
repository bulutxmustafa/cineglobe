"""Base Django settings for CineGlobe project.

These settings are shared across all environments (dev, test, prod).
Environment-specific overrides live in dev.py and prod.py.
"""

import sys
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is `backend/`
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "insecure-default-change-in-production"),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    DATABASE_URL=(str, "postgres://cineglobe:cineglobe@localhost:5432/cineglobe"),
    CACHE_BACKEND=(str, "db"),
    CACHE_MAX_ENTRIES=(int, 5000),
    COLLECTION_CACHE_TTL_SECONDS=(int, 6 * 3600),
    UPCOMING_REGION=(str, "TR"),
    UPCOMING_CACHE_TTL_SECONDS=(int, 4 * 3600),
    UPCOMING_MIN_POPULARITY=(float, 8.0),
    EMAIL_URL=(str, ""),
    DEFAULT_FROM_EMAIL=(str, "CineGlobe <no-reply@localhost>"),
    SITE_URL=(str, "http://localhost:5173"),
    CRON_SECRET=(str, ""),
    DB_CONN_MAX_AGE=(int, 0),
    CSRF_TRUSTED_ORIGINS=(list, []),
    TRUSTED_PROXY_COUNT=(int, 0),
    TMDB_API_KEY=(str, ""),
    ANTHROPIC_API_KEY=(str, ""),
    ANTHROPIC_MODEL_PARSER=(str, "claude-haiku-5-5"),
    ANTHROPIC_MODEL_EXPLAIN=(str, "claude-haiku-5-5"),
    GEMINI_API_KEY=(str, ""),
    GEMINI_MODEL=(str, "gemini-3.5-flash-lite"),
    GEMINI_FREE_TIER=(bool, True),
    LLM_PROVIDER_CHAIN=(list, ["gemini", "classic"]),
    LLM_CIRCUIT_BREAKER_SECONDS=(int, 60),
    LLM_EXPLAIN_TOP_N=(int, 3),
    GUEST_DAILY_AI_SEARCHES=(int, 10),
    USER_DAILY_AI_SEARCHES=(int, 40),
    PERSON_MIN_VOTES_MOVIE=(int, 1000),
    PERSON_MIN_VOTES_TV=(int, 300),
    PERSON_MIN_EPISODES=(int, 3),
    PERSON_LEAD_MAX_ORDER=(int, 4),
    LLM_TIMEOUT_SECONDS=(float, 20.0),
    SEARCH_CACHE_TTL_SECONDS=(int, 3600),
    LLM_DAILY_BUDGET_USD=(float, 5.0),
    SENTRY_DSN=(str, ""),
)

# Read .env file from repo root if it exists
env_file = REPO_ROOT / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

IS_TESTING = "test" in sys.argv or "pytest" in sys.modules

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.catalog",
    "apps.search",
    "apps.people",
    "apps.accounts",
    "apps.collections",
    "apps.upcoming",
    "apps.reminders",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Serves admin/static files locally; on Vercel the CDN serves them.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
# No ASGI_APPLICATION on purpose: Vercel prefers ASGI when both are set, and
# this sync DRF app is meant to run as WSGI (config/asgi.py stays for local use).

# Database & Cache configuration
if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cineglobe-test-cache",
        }
    }
else:
    DATABASES = {
        "default": env.db(
            "DATABASE_URL",
            default="postgres://cineglobe:cineglobe@localhost:5432/cineglobe",
        )
    }
    # Serverless instances share no memory: cache, quota and breaker state live
    # in the database (plan v1.8; Redis is not used). Neon: use the *pooled* URL.
    DATABASES["default"]["CONN_MAX_AGE"] = env("DB_CONN_MAX_AGE")
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
    if env("CACHE_BACKEND") == "locmem":
        CACHES = {
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        }
    else:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.db.DatabaseCache",
                "LOCATION": "django_cache",
                # Django's default of 300 entries would constantly evict TMDB
                # responses. ~20 KB/entry → ~100 MB at 5000, well inside Neon's 1 GB.
                "OPTIONS": {"MAX_ENTRIES": env("CACHE_MAX_ENTRIES")},
            }
        }

# Password validation
# Accounts (plan Faz 7, ADR-0005): e-mail sign-in, session cookie + CSRF.
AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
if IS_TESTING:
    # Argon2 is deliberately slow; tests only need a valid hash.
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
# The SPA reads the CSRF token from this cookie and sends it as X-CSRFToken.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

# E-mail: off until a free provider is chosen by the user (plan Faz 7). With no
# EMAIL_URL, mails go to the console locally and reminders use in-app only.
EMAIL_ENABLED = bool(env("EMAIL_URL"))
if EMAIL_ENABLED:
    vars().update(env.email_url("EMAIL_URL"))
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
# Public web address, used in e-mail links (password reset, unsubscribe).
SITE_URL = env("SITE_URL").rstrip("/")
# Shared secret for the daily cron endpoint (Vercel sends it as a Bearer token).
CRON_SECRET = env("CRON_SECRET")

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization (TR & EN support)
LANGUAGE_CODE = "tr"
LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
]
LOCALE_PATHS = [
    BASE_DIR / "locale",
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Locally and in tests WhiteNoise reads app static dirs directly (no collectstatic
# needed). On Vercel, collectstatic runs at build and the CDN serves STATIC_ROOT.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG or IS_TESTING

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS configuration
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    # Session cookie only (ADR-0005). Unsafe requests from signed-in users
    # must carry the CSRF token.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    # Behind a proxy (Vercel: 1) the client IP comes from X-Forwarded-For; 0 = use
    # REMOTE_ADDR. Never None: DRF would then trust any client-sent X-Forwarded-For
    # and a guest could dodge throttling and the AI-search quota by spoofing it.
    "NUM_PROXIES": env("TRUSTED_PROXY_COUNT"),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
        "health": "120/min",
        "search": "20/min",
        # Sign-in, sign-up and password reset: slow down brute force.
        "auth": "10/min",
    },
}

# drf-spectacular (OpenAPI 3.0 Documentation)
SPECTACULAR_SETTINGS = {
    "TITLE": "CineGlobe API",
    "DESCRIPTION": "CineGlobe Film & Dizi Keşif Platformu REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# External API configuration
TMDB_API_KEY = env("TMDB_API_KEY")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL_PARSER = env("ANTHROPIC_MODEL_PARSER")
ANTHROPIC_MODEL_EXPLAIN = env("ANTHROPIC_MODEL_EXPLAIN")
GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL")
GEMINI_FREE_TIER = env("GEMINI_FREE_TIER")

# LLM provider chain & cost guard (plan §3.10)
LLM_PROVIDER_CHAIN = [p.strip().lower() for p in env("LLM_PROVIDER_CHAIN") if p.strip()]
LLM_CIRCUIT_BREAKER_SECONDS = env("LLM_CIRCUIT_BREAKER_SECONDS")
LLM_EXPLAIN_TOP_N = env("LLM_EXPLAIN_TOP_N")
GUEST_DAILY_AI_SEARCHES = env("GUEST_DAILY_AI_SEARCHES")
USER_DAILY_AI_SEARCHES = env("USER_DAILY_AI_SEARCHES")
# Daily quotas and the budget reset at local midnight.
QUOTA_TIME_ZONE = "Europe/Istanbul"

# People ranking rules (plan §3.2)
PERSON_MIN_VOTES_MOVIE = env("PERSON_MIN_VOTES_MOVIE")
PERSON_MIN_VOTES_TV = env("PERSON_MIN_VOTES_TV")
# A series counts as a real role only from this many episodes (guest spots excluded).
PERSON_MIN_EPISODES = env("PERSON_MIN_EPISODES")
# Movie billing order 0..4 = top-5 cast ("lead").
PERSON_LEAD_MAX_ORDER = env("PERSON_LEAD_MAX_ORDER")
LLM_DAILY_BUDGET_USD = env("LLM_DAILY_BUDGET_USD")
LLM_TIMEOUT_SECONDS = env("LLM_TIMEOUT_SECONDS")
SEARCH_CACHE_TTL_SECONDS = env("SEARCH_CACHE_TTL_SECONDS")
COLLECTION_CACHE_TTL_SECONDS = env("COLLECTION_CACHE_TTL_SECONDS")
# Release dates move: short cache (plan §3.7: 3–6 hours).
UPCOMING_REGION = env("UPCOMING_REGION")
UPCOMING_CACHE_TTL_SECONDS = env("UPCOMING_CACHE_TTL_SECONDS")
UPCOMING_MIN_POPULARITY = env("UPCOMING_MIN_POPULARITY")
SENTRY_DSN = env("SENTRY_DSN")
