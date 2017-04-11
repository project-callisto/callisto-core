from wizard_builder.models import QuestionPage

from django.contrib.sites.models import Site
from django.test import TestCase


class SitePageTest(TestCase):

    def test_basic_created_question_page_comes_with_a_site(self):
        page = QuestionPage.objects.create()
        self.assertEqual(page.site.domain, 'example.com')

    def test_on_site_increments_for_default_site(self):
        count_before = QuestionPage.objects.on_site().count()
        page = QuestionPage.objects.create()
        count_after = QuestionPage.objects.on_site().count()
        self.assertEqual(count_before + 1, count_after)

    def test_on_site_does_not_increment_for_alternate_site(self):
        count_before = QuestionPage.objects.on_site().count()
        page = QuestionPage.objects.create()
        page.site = Site.objects.create()
        page.save()
        count_after = QuestionPage.objects.on_site().count()
        self.assertEqual(count_before, count_after)
