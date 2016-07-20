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
    "callisto.delivery",
    "callisto.evaluation"
]

SITE_ID = 1

MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',)

SCHOOL_REPORT_PREFIX = "000"

# This low number is for testing purposes only, and is insufficient for production by several orders of magnitude
KEY_ITERATIONS = 100


def get_test_key():
    with open(os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))),
                           'test_publickey.gpg'), 'r') as key_file:
        key_str = key_file.read()
    return key_str

COORDINATOR_NAME = "Tatiana Nine"
COORDINATOR_EMAIL = "titleix@example.com"
COORDINATOR_PUBLIC_KEY = get_test_key()

SCHOOL_SHORTNAME = "test"
SCHOOL_LONGNAME = "test"
APP_URL = "test"

PASSWORD_MINIMUM_ENTROPY = 35

SECRET_KEY = "not needed"

CALLISTO_EVAL_PUBLIC_KEY = get_test_key()

DECRYPT_THROTTLE_RATE = '100/m'

MATCH_IMMEDIATELY = True

PEPPER = os.urandom(32)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': ['%s/templates' % os.path.abspath(os.path.dirname(__file__))]
    },
]
