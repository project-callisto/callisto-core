import os
os.environ["DJANGO_SETTINGS_MODULE"] = "wizard_builder.tests.test_app.heroku_settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
