from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings
from django.test import override_settings

from callisto.notification.models import EmailNotification


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
        index = 0
        for i in range(site_1_pages):
            EmailNotification.objects.create(name=index)
            index += 1
        for i in range(site_2_pages):
            notification = EmailNotification.objects.create(name=index)
            notification.sites.add(site_2) # site_1 is already added
            index += 1

        self.assertEqual(EmailNotification.objects.on_site().count(), site_1_pages + site_2_pages)
        with TempSiteID(site_2.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_2_pages)

    def test_multiple_added_sites_are_reflected_by_on_site(self):
        site_2 = Site.objects.create()
        notification = EmailNotification.objects.create()
        notification.sites.add(site_2)

        self.assertIn(notification, EmailNotification.objects.on_site())
        with TempSiteID(site_2.id):
            self.assertIn(notification, EmailNotification.objects.on_site())
