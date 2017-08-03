import dj_database_url

from wizard_builder.tests.test_app.settings import *

DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
}

ALLOWED_HOSTS = [APP_URL]
