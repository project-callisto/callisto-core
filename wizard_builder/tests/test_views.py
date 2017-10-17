from copy import copy
from unittest import mock, skip

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import models, view_helpers


class FormPersistenceTest(TestCase):
    fixtures = [
        'wizard_builder_data',
    ]
    form_key = view_helpers.StorageHelper.storage_form_key

    def setUp(self):
        super().setUp()
        self.data = {'question_2': 'aloe ipsum speakerbox'}
        self.wizard_url = reverse(
            'wizard_update',
            kwargs={'step': '0'},
        )
        self.initial_response = self.client.get(self.wizard_url)

    def _change_form_text(self, form):
        question = models.FormQuestion.objects.filter(pk=form['id'])
        question.update(text='text should be persistent')

    def test_session_forms_identical_between_requests(self):
        form_before = self.client.session[self.form_key]
        self.client.get(self.wizard_url)
        form_after = self.client.session[self.form_key]
        self.assertEqual(form_before, form_after)

    def test_user_form_identical_when_backend_form_changed(self):
        form_before = self.client.session[self.form_key]
        question_text = form[0][0]['question_text']
        self._change_form_text(form_before[0][0])
        self.client.get(self.wizard_url)
        form_after = self.client.session[self.form_key]
        self.assertEqual(form_before, form_after)
        self.assertEqual(question_text, form_after[0][0]['question_text'])

    def test_when_changed_and_post(self):
        form_before = self.client.session[self.form_key]
        question_text = form_before[0][0]['question_text']
        question_pk = form_before[0][0]['id']
        question = models.FormQuestion.objects.filter(pk=question_pk)
        question.update(text='text should be persistent')
        self.client.post(self.wizard_url, self.data)
        form_after = self.client.session[self.form_key]
        self.assertEqual(form_before, form_after)
        self.assertNotEqual(
            'text should be persistent',
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
            'text should be persistent',
            form_after[0]['question_text'],
        )
        self.assertEqual(form_before, form_after)


class ViewTest(TestCase):
    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        super().setUp()
        self.step = '1'
        self.data = {'question_2': 'aloe ipsum speakerbox'}
        self.url = reverse(
            'wizard_update',
            kwargs={'step': self.step},
        )
        self.choice_url = reverse(
            'wizard_update',
            kwargs={'step': '0'},
        )
        self.review_url = reverse(
            'wizard_update',
            kwargs={'step': view_helpers.StepsHelper.done_name},
        )

    def test_storage_receives_post_data(self):
        self.client.post(self.url, self.data)
        self.assertEqual(
            self.client.session[view_helpers.StorageHelper.storage_data_key],
            self.data,
        )

    def test_storage_populates_form_data(self):
        self.client.post(self.url, self.data)
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertEqual(
            form.data,
            self.data,
        )

    def test_form_data_wizard_goto_step_regression(self):
        data_with_goto_step = copy(self.data)
        data_with_goto_step['wizard_goto_step'] = 'Next'
        self.client.post(self.url, data_with_goto_step)
        response = self.client.get(self.url)
        form_data = response.context['form'].data
        expected_data = self.data
        self.assertEqual(
            form_data,
            expected_data,
        )

    def test_review_page_textbox(self):
        self.client.post(self.url, self.data)
        response = self.client.get(self.review_url)
        form_data = response.context['form_data']
        self.assertIn(
            {'do androids dream of electric sheep?':
                ['aloe ipsum speakerbox'],
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
