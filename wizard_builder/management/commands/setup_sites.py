from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def _setup_current_site(self):
        if getattr(settings, 'HEROKU_REVIEW_APP_DOMAIN', None):
            current_domain = settings.HEROKU_REVIEW_APP_DOMAIN
        else:
            current_domain = settings.APP_URL
        Site.objects.exclude(id=1).delete()
        Site.objects.filter(id=1).update(domain=current_domain)

    def _setup_allowed_hosts(self):
        if getattr(settings, 'ALLOWED_HOSTS', None):
            for host in settings.ALLOWED_HOSTS:
                Site.objects.get_or_create(domain=host)

    def handle(self, *args, **options):
        self._setup_current_site()
        self._setup_allowed_hosts()
