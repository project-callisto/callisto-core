import os
import sys

from wizard_builder.tests.settings import *

# add wizard_builder folder to path
# needed to add wizard_builder to INSTALLED_APPS
base_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../../')
sys.path.append(base_dir)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "wizard_builder.test_app.sqlite3",
    }
}

WIZARD_BUILDER_DISABLE_DOWNCASTING = True
