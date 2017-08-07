import dj_database_url
from wizard_builder.tests.test_app.live_settings import *

DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
}

if os.getenv('HEROKU_APP_NAME', default=''):
    HEROKU_REVIEW_APP_DOMAIN = os.getenv('HEROKU_APP_NAME') + '.herokuapp.com'
else:
    HEROKU_REVIEW_APP_DOMAIN = ''

ALLOWED_HOSTS = [
    APP_URL,
    HEROKU_REVIEW_APP_DOMAIN,
]
