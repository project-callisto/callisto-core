import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **options):
        from django.conf import settings
        from django.contrib.sites.models import Site
        if getattr(settings, 'ALLOWED_HOSTS'):
            for host in settings.ALLOWED_HOSTS:
                Site.objects.get_or_create(domain=host)
        else:
            Site.objects.get_or_create(domain=settings.APP_URL)
