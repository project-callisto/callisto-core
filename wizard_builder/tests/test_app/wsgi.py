import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wizard_builder.tests.test_app.heroku_settings")

application = get_wsgi_application()
