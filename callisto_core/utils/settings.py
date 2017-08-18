import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = os.getenv("SECRET_KEY", default='secret key')
DEBUG = True

ROOT_URLCONF = "callisto_core.utils.urls"
APP_URL = os.environ.get('APP_URL', 'localhost')


def load_file(path):
    path = os.path.join(BASE_DIR, path)
    with open(path, 'r') as file_data:
        data = file_data.read()
    return data


TIME_ZONE = 'UTC'
USE_TZ = True


COORDINATOR_NAME = "COORDINATOR_NAME"
COORDINATOR_EMAIL = 'COORDINATOR_EMAIL@example.com'
SCHOOL_SHORTNAME = "SCHOOL_SHORTNAME"
SCHOOL_LONGNAME = "SCHOOL_LONGNAME"
SCHOOL_REPORT_PREFIX = 1
CALLISTO_EVAL_PUBLIC_KEY = ""
MATCH_IMMEDIATELY = True
COORDINATOR_PUBLIC_KEY = load_file('callisto_publickey.gpg')
CALLISTO_EVAL_PUBLIC_KEY = load_file('callisto_publickey.gpg')

KEY_HASHERS = [
    "callisto_core.delivery.hashers.Argon2KeyHasher",
    "callisto_core.delivery.hashers.PBKDF2KeyHasher"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        'NAME': 'db-default.sqlite3',
    },
    "alternate": {
        "ENGINE": "django.db.backends.sqlite3",
        'NAME': 'db-alternate.sqlite3',
    },
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'nested_admin',
    'tinymce',
    'widget_tweaks',
    'wizard_builder',
    'callisto_core.delivery',
    'callisto_core.evaluation',
    'callisto_core.notification',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

KEY_ITERATIONS = 100
ORIGINAL_KEY_ITERATIONS = 100000
ARGON2_TIME_COST = 2
ARGON2_MEM_COST = 512
ARGON2_PARALLELISM = 2
PEPPER = os.urandom(32)
DECRYPT_THROTTLE_RATE = '100/m'
PASSWORD_MINIMUM_ENTROPY = 35

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%I:%M %p %A(%d) %B(%m) %Y %Z',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'gnupg':{
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='INFO'),
        },
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='DEBUG'),
        },
        'django.template': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='INFO'),
        },
        'django.db.backends': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='INFO'),
        },
        'selenium': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='WARNING'),
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', default='DEBUG'),
    },
}
