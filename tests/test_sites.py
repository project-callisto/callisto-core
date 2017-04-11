from wizard_builder.models import QuestionPage

from django.test import TestCase


class SitePageTest(TestCase):

    def test_basic_created_question_page_comes_with_a_site(self):
        page = QuestionPage.objects.create()
        self.assertEqual(page.site.domain, 'example.com')
