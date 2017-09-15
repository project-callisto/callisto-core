from mock import patch

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from ..models import Page, SingleLineText


class TempSiteID():
    '''
        with TempSiteID(1):
            ...
    '''

    def __init__(self, site_id):
        self.site_id_temp = site_id

    def __enter__(self):
        self.site_id_stable = getattr(settings, 'SITE_ID', None)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable


class SiteIDTest(TestCase):

    @override_settings()
    def test_page_has_no_default_site_attribute(self):
        with TempSiteID(1):
            page = Page.objects.create()
        self.assertEqual(page.sites.count(), 0)

    @override_settings()
    def test_on_site_respects_SITE_ID_setting(self):
        site_1_pages = 3
        site_2_pages = site_1_pages + 1
        site_1 = Site.objects.get(id=1)
        site_2 = Site.objects.create()

        for i in range(site_1_pages):
            page = Page.objects.create()
            page.sites.add(site_1.id)
        for i in range(site_2_pages):
            page = Page.objects.create()
            page.sites.add(site_2.id)

        with TempSiteID(site_1.id):
            self.assertEqual(Page.objects.on_site().count(), site_1_pages)
        with TempSiteID(site_2.id):
            self.assertEqual(Page.objects.on_site().count(), site_2_pages)

    @override_settings()
    def test_can_override_site_id_when_setting_is_set(self):
        with TempSiteID(1):
            site_2 = Site.objects.create()
            page = Page.objects.create()
            page.sites.add(site_2.id)
            self.assertNotEqual(settings.SITE_ID, site_2.id)
            self.assertNotEqual(page.sites.first().id, settings.SITE_ID)

        self.assertEqual(page.sites.first().id, site_2.id)
