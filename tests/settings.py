import os

DEBUG = True

USE_TZ = True
REPORT_TIME_ZONE = 'Europe/Paris'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    },
    # used to test multiple database support
    "alternate": {
        "ENGINE": "django.db.backends.sqlite3",
    },
}


ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "wizard_builder",
    "callisto.delivery",
    "callisto.evaluation",
    "callisto.notification",
]

SITE_ID = 1

MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',)

SCHOOL_REPORT_PREFIX = "000"

KEY_HASHERS = [
    "callisto.delivery.hashers.Argon2KeyHasher",
    "callisto.delivery.hashers.PBKDF2KeyHasher"
]

# This low number is for testing purposes only, and is insufficient for production by several orders of magnitude
KEY_ITERATIONS = 100
ORIGINAL_KEY_ITERATIONS = 100000

ARGON2_TIME_COST = 2
ARGON2_MEM_COST = 512
ARGON2_PARALLELISM = 2


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
