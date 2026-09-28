"""Development settings for CineGlobe project.

Used during local development and testing.
"""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env

DEBUG = env.bool("DJANGO_DEBUG", default=True)

# In development, also enable browsable API for easy debugging
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Allow all origins in dev if specifically needed, otherwise keep configured origins
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Email backend: print to console in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
