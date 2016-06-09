import os

DEBUG = True

USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('db_name', default='callisto'),
        'USER': os.environ.get('db_user', default=''),
        'PASSWORD': os.environ.get('db_pass', default=''),
        'HOST': os.environ.get('db_host', default='127.0.0.1'),
        'PORT': os.environ.get('db_port', default='5432')
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

MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',)

TEMPLATE_DIRS = ['%s/tests/templates' % os.path.abspath(os.path.dirname(__file__))]

SCHOOL_REPORT_PREFIX = "000"

KEY_ITERATIONS = 100

COORDINATOR_NAME = "test"

SCHOOL_SHORTNAME = "test"

PASSWORD_MINIMUM_ENTROPY = 35

SECRET_KEY = "not needed"

def get_test_key():
    with open(os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))),
                           'test_publickey.gpg'), 'r') as key_file:
        key_str = key_file.read()
    return key_str

CALLISTO_EVAL_PUBLIC_KEY = os.environ.get('CALLISTO_EVAL_PUBLIC_KEY', get_test_key())
