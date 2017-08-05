import dj_database_url
from wizard_builder.tests.test_app.live_settings import *

DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
}

ALLOWED_HOSTS = [
    APP_URL,
    os.getenv('HEROKU_APP_NAME', default=''),
    os.getenv('HEROKU_PARENT_APP_NAME', default=''),
]
