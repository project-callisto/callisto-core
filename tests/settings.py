import os

DEBUG = True

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "wizard_builder",
    "tests.test_app"
]

SITE_ID = 1

MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',)

TEMPLATE_DIRS = ['%s/test_app/templates' % os.path.abspath(os.path.dirname(__file__))]

SECRET_KEY = "not important"
