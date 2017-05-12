from wizard_builder.models import QuestionPage, SingleLineText

from django.test import TestCase


class InheritenceTest(TestCase):

    def test_question_page_instance(self):
        page = QuestionPage.objects.create()
        question = SingleLineText.objects.create(page=page)
        self.assertTrue(isinstance(question.page, QuestionPage))

    def test_page_form_question_set_instance(self):
        page = QuestionPage.objects.create()
        SingleLineText.objects.create(page=page)
        question = QuestionPage.objects.first().formquestion_set.first()
        self.assertTrue(isinstance(question.page, SingleLineText))
