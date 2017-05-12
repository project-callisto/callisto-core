from wizard_builder.models import QuestionPage, SingleLineText

from django.test import TestCase


class InheritenceTest(TestCase):

    def test_site_passed_to_question_page_manager(self):
        page = QuestionPage.objects.create()
        question = SingleLineText.objects.create(page_id=page.id)
        self.assertTrue(isinstance(question.page, QuestionPage))
