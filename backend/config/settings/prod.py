"""Production settings for CineGlobe project.

Hardened security, disabled debug mode, strict host checks.
"""

from .base import *  # noqa: F403
from .base import SECRET_KEY, SENTRY_DSN, env

DEBUG = False

# Ensure SECRET_KEY is not default
if SECRET_KEY in ("insecure-default-change-in-production", "change-me"):
    raise ValueError(
        "DJANGO_SECRET_KEY must be properly set in production environment!"
    )

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Sentry error tracking
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        send_default_pii=False,
    )
