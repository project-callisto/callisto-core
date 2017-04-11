from callisto.notification.models import EmailNotification

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase


class TempSiteID():
    '''
        with TempSiteID(1):
            ...
    '''

    def __init__(self, site_id):
        self.site_id_temp = site_id

    def __enter__(self):
        self.site_id_stable = getattr(settings, 'SITE_ID', 1)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable


class SitePageTest(TestCase):

    def test_on_site_respects_SITE_ID_setting(self):
        site_1_pages = 3
        site_2_pages = site_1_pages + 1
        site_2 = Site.objects.create()
        for i in range(site_1_pages):
            EmailNotification.objects.create()
        for i in range(site_2_pages):
            EmailNotification.objects.create(site=site_2)

        self.assertEqual(EmailNotification.objects.on_site().count(), site_1_pages)
        with TempSiteID(site_2.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_2_pages)
