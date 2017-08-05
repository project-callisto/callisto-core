import sys

from wizard_builder.tests.test_settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "wizard_builder.test_app.sqlite3",
    }
}
