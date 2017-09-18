import os
import subprocess

from django.test import TestCase

from ..models import Choice, MultipleChoice, Page, SingleLineText


class InheritanceTest(TestCase):

    def test_page_form_question_set_instance(self):
        page = Page.objects.create()
        SingleLineText.objects.create(page_id=page.id)
        question = Page.objects.first().formquestion_set.first()
        self.assertIsInstance(question, SingleLineText)

    def test_choice_multiple_choice_instance(self):
        page = Page.objects.create()
        question = MultipleChoice.objects.create(page_id=page.id)
        Choice.objects.create(question_id=question.id)
        choice = Choice.objects.first()
        self.assertIsInstance(choice.question, MultipleChoice)


class DumpdataHackTest(TestCase):

    def test_dumpdata_hack(self):
        Page.objects.using('dumpdata_db').delete()
        Page.objects.using('dumpdata_db').get_or_create(id=1)
        subprocess.check_call('''
            DJANGO_SETTINGS_MODULE='wizard_builder.tests.test_app.ops_settings' \
                python manage.py dumpdata \
                    wizard_builder \
                    -o wizard_builder/tests/test_app/test-dump.json \
                    --natural-foreign \
                    --indent 2 \
                    --database dumpdata_db
        ''', shell=True)

        subprocess.check_call('''
            DJANGO_SETTINGS_MODULE='wizard_builder.tests.test_app.ops_settings' \
                python manage.py loaddata \
                    wizard_builder/tests/test_app/test-dump.json \
                    --database dumpdata_db
        ''', shell=True)

        with open('wizard_builder/tests/test_app/test-dump.json', 'r') as dump_file:
            dump_file_contents = dump_file.read()
        self.assertIn('wizard_builder.page', dump_file_contents)
        self.assertEqual(Page.objects.using('dumpdata_db').count(), 1)
