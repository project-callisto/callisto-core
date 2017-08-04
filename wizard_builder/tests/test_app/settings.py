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

APP_URL = os.environ.get('APP_URL', 'localhost')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
