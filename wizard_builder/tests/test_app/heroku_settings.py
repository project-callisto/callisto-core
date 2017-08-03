import dj_database_url

from wizard_builder.tests.test_app.settings import *

# STATIC FILES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

DEBUG = False

DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
}

ALLOWED_HOSTS = [APP_URL]

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
        'django':{
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='DEBUG'),
        },
        'django.template':{
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('LOG_LEVEL', default='INFO'),
        },
    },
    # controls the base log level, set like LOG_LEVEL='ERROR'
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', default='DEBUG'),
    },
}
