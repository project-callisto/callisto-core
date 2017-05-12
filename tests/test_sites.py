from mock import patch
from wizard_builder.models import PageBase, QuestionPage, SingleLineText

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
        self.site_id_stable = getattr(settings, 'SITE_ID', None)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable


class SiteIDTest(TestCase):

    def test_page_has_defaualt_site_attribute(self):
        with TempSiteID(1):
            page = QuestionPage.objects.create()
        self.assertEqual(page.site.domain, 'example.com')

    def test_on_site_respects_SITE_ID_setting(self):
        site_1_pages = 3
        site_2_pages = site_1_pages + 1
        site_2 = Site.objects.create()
        with TempSiteID(1):
            for i in range(site_1_pages):
                QuestionPage.objects.create()
            for i in range(site_2_pages):
                with TempSiteID(site_2.id):
                    QuestionPage.objects.create()
            self.assertEqual(QuestionPage.objects.on_site().count(), site_1_pages)

        with TempSiteID(site_2.id):
            self.assertEqual(QuestionPage.objects.on_site().count(), site_2_pages)

    def test_can_override_default_site_id(self):
        with TempSiteID(1):
            page = QuestionPage.objects.create()
            self.assertEqual(page.site.id, settings.SITE_ID)

        site_2 = Site.objects.create()
        page.site = site_2
        page.save()
        self.assertEqual(page.site_id, site_2.id)
        self.assertEqual(page.site.id, site_2.id)
        self.assertNotEqual(settings.SITE_ID, site_2.id)


class SiteRequestTest(TestCase):

    def setUp(self):
        super(SiteRequestTest, self).setUp()
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        self.page = QuestionPage.objects.create(site_id=self.site.id)
        self.question = SingleLineText.objects.create(text="first question", page=self.page)

    @patch('wizard_builder.managers.PageBaseQuerySet.on_site')
    def test_site_passed_to_question_page_manager(self, mock_on_site):
        mock_on_site.return_value = PageBase.objects.filter(id=self.page.id)
        self.client.get('/wizard/new/0/')
        mock_on_site.assert_called_with(self.site.id)
