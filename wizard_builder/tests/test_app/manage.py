#!/usr/bin/env python
import os
import sys

def setup_sites():
    from django.conf import settings
    from django.contrib.sites.models import Site
    Site.objects.get_or_create(domain=settings.APP_URL)

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

    setup_sites()
