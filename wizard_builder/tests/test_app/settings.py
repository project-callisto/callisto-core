import os
import sys

# add wizard_builder folder to path
base_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../../')
sys.path.append(base_dir)

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

WIZARD_BUILDER_DISABLE_DOWNCASTING = True
