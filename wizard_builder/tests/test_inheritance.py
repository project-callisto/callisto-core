import subprocess

from django.test import TestCase

from ..models import (
    Choice, Conditional, FormQuestion, MultipleChoice, PageBase, QuestionPage,
    SingleLineText,
)


class InheritanceTest(TestCase):

    def test_question_page_instance(self):
        page = QuestionPage.objects.create()
        SingleLineText.objects.create(page_id=page.id)
        question = FormQuestion.objects.first()
        self.assertIsInstance(question.page, QuestionPage)

    def test_page_form_question_set_instance(self):
        page = QuestionPage.objects.create()
        SingleLineText.objects.create(page_id=page.id)
        question = PageBase.objects.first().formquestion_set.first()
        self.assertIsInstance(question, SingleLineText)

    def test_choice_multiple_choice_instance(self):
        page = QuestionPage.objects.create()
        question = MultipleChoice.objects.create(page_id=page.id)
        Choice.objects.create(question_id=question.id)
        choice = Choice.objects.first()
        self.assertIsInstance(choice.question, MultipleChoice)

    def test_conditional_instance(self):
        page = QuestionPage.objects.create()
        question = MultipleChoice.objects.create(page_id=page.id)
        Conditional.objects.create(question_id=question.id, page_id=page.id)
        condition = Conditional.objects.first()
        self.assertTrue(QuestionPage.objects.first().conditional)
        self.assertIsInstance(condition.question, MultipleChoice)
        self.assertIsInstance(condition.page, QuestionPage)


class DumpdataHackTest(TestCase):

    def test_dumpdata_hack(self):
        QuestionPage.objects.using('test_app').create()

        subprocess.check_call('''
            python wizard_builder/tests/test_app/manage.py \
                dumpdata \
                    wizard_builder \
                    -o wizard_builder/tests/test_app/test-dump.json \
                    --natural-foreign \
                    --indent 2
        ''', shell=True)

        subprocess.check_call('''
            python wizard_builder/tests/test_app/manage.py \
                loaddata \
                    wizard_builder/tests/test_app/test-dump.json
        ''', shell=True)

        with open('wizard_builder/tests/test_app/test-dump.json', 'r') as dump_file:
            dump_file_contents = dump_file.read()
        self.assertIn('wizard_builder.questionpage', dump_file_contents)
        self.assertIn('wizard_builder.pagebase', dump_file_contents)
        self.assertEqual(PageBase.objects.using('test_app').count(), 1)
        self.assertEqual(QuestionPage.objects.using('test_app').count(), 1)
