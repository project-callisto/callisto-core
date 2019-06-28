from copy import copy
from unittest import mock, skip

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from callisto_core.tests import test_base
from callisto_core.wizard_builder import models, view_helpers


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class FormPersistenceTest(
    test_base.ReportFlowHelper,
):

    fixtures = [
        'wizard_builder_data',
    ]
    form_key = view_helpers.StorageHelper.storage_form_key

    def setUp(self):
        super().setUp()
        response = self.client_post_report_creation()
        self.uuid = response.context['report'].uuid
        self.data = {'question_2': 'aloe ipsum speakerbox'}
        self.wizard_url = reverse(
            'report_update',
            kwargs={'step': '0', 'uuid': self.uuid},
        )
        self.initial_response = self.client.get(self.wizard_url)

    def _change_form_text(self, form):
        question = models.FormQuestion.objects.filter(pk=form['id'])
        question.update(text='this text is not persistent')

    def test_session_forms_identical_between_requests(self):
        form_before = self.decrypted_report[self.form_key]
        self.client.get(self.wizard_url)
        form_after = self.decrypted_report[self.form_key]
        self.assertEqual(form_before, form_after)

    def test_user_form_identical_when_backend_form_changed(self):
        form_before = self.decrypted_report[self.form_key]
        question_text = form_before[0][0]['question_text']
        self._change_form_text(form_before[0][0])
        self.client.get(self.wizard_url)
        form_after = self.decrypted_report[self.form_key]
        self.assertEqual(form_before, form_after)
        self.assertEqual(question_text, form_after[0][0]['question_text'])

    def test_when_changed_and_post(self):
        form_before = self.decrypted_report[self.form_key]
        question_text = form_before[0][0]['question_text']
        question_pk = form_before[0][0]['id']
        question = models.FormQuestion.objects.filter(pk=question_pk)
        question.update(text='this text is not persistent')
        self.client.post(self.wizard_url, self.data)
        form_after = self.decrypted_report[self.form_key]
        self.assertEqual(form_before, form_after)
        self.assertNotEqual(
            'this text is not persistent',
            form_after[0][0]['question_text'],
        )
        self.assertEqual(question_text, form_after[0][0]['question_text'])

    def test_response_forms_identical(self):
        form_before = self.initial_response.context['form'].serialized
        response = self.client.get(self.wizard_url)
        form_after = response.context['form'].serialized
        self.assertEqual(form_before, form_after)

    def test_response_forms_identical_when_form_changed(self):
        form_before = self.initial_response.context['form'].serialized
        self._change_form_text(form_before[0])
        response = self.client.get(self.wizard_url)
        form_after = response.context['form'].serialized
        self.assertNotEqual(
            'this text is not persistent',
            form_after[0]['question_text'],
        )
        self.assertEqual(form_before, form_after)


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ViewTest(
    test_base.ReportFlowHelper,
):
    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        super().setUp()
        response = self.client_post_report_creation()
        self.uuid = response.context['report'].uuid
        self.step = '1'
        self.data = {'question_2': 'aloe ipsum speakerbox'}
        self.url = reverse(
            'report_update',
            kwargs={'step': self.step, 'uuid': self.uuid},
        )
        self.choice_url = reverse(
            'report_update',
            kwargs={'step': '0', 'uuid': self.uuid},
        )
        self.review_url = reverse(
            'report_update',
            kwargs={
                'step': view_helpers.StepsHelper.done_name,
                'uuid': self.uuid},
        )
        self.response = self.client_post_answer_question()

    def test_storage_populates_form_data(self):
        response = self.client_post_answer_question()
        form = response.context['form']
        self.assertEqual(
            form.data['question_3'],
            self.data['question_3'],
        )

    def test_review_page_textbox(self):
        self.client_post_answer_question()
        response = self.client.get(self.review_url)
        form_data = response.context['form_data']
        self.assertIn(
            {'eat it now???':
                ['blanket ipsum pillowfight'],
             },
            form_data,
        )

    def test_review_page_choice(self):
        choice_data = {'question_1': ['3']}
        self.client.post(self.choice_url, choice_data)
        response = self.client.get(self.review_url)
        form_data = response.context['form_data']
        self.assertIn(
            {'food options': ['sugar']},
            form_data,
        )

    @skip('WIP')
    def test_review_page_choice_extra_info(self):
        choice_data = {
            'question_1': ['1'],
            'extra_info': 'beets',
        }
        self.client.post(self.choice_url, self.data)
        response = self.client.get(self.review_url)
        form_data = response.context['form_data']
        self.assertIn(
            {'food options': ['sugar: beets']},
            form_data,
        )
