from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

os.environ["DJANGO_SETTINGS_MODULE"] = "heroku_settings"
