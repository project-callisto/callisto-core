import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = os.getenv("passphrase", default="secret key")
DEBUG = True
SITE_ID = 1

ROOT_URLCONF = "callisto_core.utils.urls"
APP_URL = os.environ.get("APP_URL", "localhost")
LOGIN_REDIRECT_URL = "/reports/new/"


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 120


def load_file(path):
    path = os.path.join(BASE_DIR, path)
    with open(path, "r") as file_data:
        data = file_data.read()
    return data

CALLISTO_API_ENDPOINT = "callisto_core.tests.utils.api"
CALLISTO_EVAL_PUBLIC_KEY = load_file("callisto_publickey.gpg")
CALLISTO_MATCHING_API = "callisto_core.tests.utils.api.CustomMatchingApi"
CALLISTO_NOTIFICATION_API = "callisto_core.tests.utils.api.CustomNotificationApi"
CALLISTO_TENANT_API = "callisto_core.tests.utils.api.CustomTenantApi"

KEY_HASHERS = [
    "callisto_core.delivery.hashers.Argon2KeyHasher",
    "callisto_core.delivery.hashers.PBKDF2KeyHasher",
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "callisto-core"}
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    "nested_admin",
    "widget_tweaks",
    "callisto_core.wizard_builder",
    "callisto_core.delivery",
    "callisto_core.evaluation",
    "callisto_core.notification",
    "callisto_core.reporting",
    "callisto_core.accounts",
    "callisto_core.celeryconfig",
    "callisto_core.utils",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",  # Sets request.site
]

KEY_ITERATIONS = 100
ORIGINAL_KEY_ITERATIONS = 100000
ARGON2_TIME_COST = 2
ARGON2_MEM_COST = 512
ARGON2_PARALLELISM = 2
PEPPER = os.urandom(32)
DECRYPT_THROTTLE_RATE = "100/m"
PASSWORD_MINIMUM_ENTROPY = 35

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "staticfiles"))
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            "datefmt": "%I:%M %p %A(%d) %B(%m) %Y %Z",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "gnupg": {"handlers": ["console"], "propagate": False, "level": "INFO"},
        "django.db": {"handlers": ["console"], "propagate": False, "level": "INFO"},
        "django": {"handlers": ["console"], "propagate": False, "level": "DEBUG"},
        "django.template": {
            "handlers": ["console"],
            "propagate": False,
            "level": "WARNING",
        },
        "django.db.backends": {
            "handlers": ["console"],
            "propagate": False,
            "level": "INFO",
        },
        "selenium": {"handlers": ["console"], "propagate": False, "level": "INFO"},
        "gnupg": {"handlers": ["console"], "propagate": False, "level": "ERROR"},
        "PIL": {"handlers": ["console"], "propagate": False, "level": "ERROR"},
        "parso": {"handlers": [], "propagate": False},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", default="INFO")},
}

# Configs for celery testing
CELERY_TASK_SERIALIZER = "json"
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_BACKEND = "memory"
CELERY_BROKER_URL = "memory://"

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", default="")
INDEXING_KEY = os.getenv("INDEXING_KEY", "notsettingthiswillbreakyou")
