DEBUG = True

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tests/test_app/default.sqlite3",
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    "django.contrib.sites",
    "wizard_builder",
]

SECRET_KEY = "not important"

MIDDLEWARE_CLASSES = ()
