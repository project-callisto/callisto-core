import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):

    def _setup_allowed_hosts(self):
        if getattr(settings, 'ALLOWED_HOSTS', None):
            for host in settings.ALLOWED_HOSTS:
                Site.objects.get_or_create(domain=host)

    def _setup_current_site(self):
        if getattr(settings, 'HEROKU_APP_NAME', None):
            current_domain = settings.HEROKU_APP_NAME
        else:
            current_domain = settings.APP_URL
        Site.objects.filter(
            id=1,
        ).update(
            domain=current_domain,
        )

    def handle(self, *args, **options):
        self._setup_allowed_hosts()
        self._setup_current_site()
