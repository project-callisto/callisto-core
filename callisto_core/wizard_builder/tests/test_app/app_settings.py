import sys

from wizard_builder.tests.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "wizard_builder_test_app.sqlite3",
    },
}
