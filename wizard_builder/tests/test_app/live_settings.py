from wizard_builder.tests.test_app.app_settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    },
}

DEBUG = False
MIDDLEWARE_CLASSES = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE_CLASSES
