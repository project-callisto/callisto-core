from wizard_builder.models import (
    QuestionPage, SingleLineText, Choice, MultipleChoice
)
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

    def test_choice_multiple_choice_instance(self):
        page = QuestionPage.objects.create()
        question = MultipleChoice.objects.create(page=page)
        choice = Choice.objects.create(question=question)
        self.assertTrue(isinstance(choice.question, MultipleChoice))
