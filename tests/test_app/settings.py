DEBUG = True

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "wizard_builder_default_test",
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    "django.contrib.sites",
    "wizard_builder",
]

SECRET_KEY = "not important"

MIDDLEWARE_CLASSES = ()
