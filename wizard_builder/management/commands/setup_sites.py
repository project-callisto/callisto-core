from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def _setup_current_site(self):
        if os.getenv('HEROKU_APP_NAME', default=''):
            review_app_domain = os.getenv('HEROKU_APP_NAME') + '.herokuapp.com'
        else:
            review_app_domain = ''
        if review_app_domain:
            current_domain = settings.review_app_domain
        else:
            current_domain = settings.APP_URL
        Site.objects.filter(domain=current_domain).exclude(id=1).delete()
        Site.objects.filter(id=1).update(domain=current_domain)

    def handle(self, *args, **options):
        self._setup_current_site()
