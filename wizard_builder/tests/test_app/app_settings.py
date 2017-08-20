import sys

from wizard_builder.tests.test_settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "wizard_builder_test_app.sqlite3",
    },
    "dumpdata_db": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": 'wizard_builder_dumpdata_db.sqlite3',
    },
}
