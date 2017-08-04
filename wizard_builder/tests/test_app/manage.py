#!/usr/bin/env python
import os
import sys


def setup_sites():
    from django.conf import settings
    from django.contrib.sites.models import Site
    if getattr(settings, 'ALLOWED_HOSTS'):
        for host in settings.ALLOWED_HOSTS:
            Site.objects.get_or_create(domain=host)
    else:
        Site.objects.get_or_create(domain=settings.APP_URL)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
    setup_sites()


if __name__ == "__main__":
    main()
