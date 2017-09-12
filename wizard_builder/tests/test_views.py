from copy import copy
from unittest import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import view_helpers


class ViewTest(TestCase):
    fixtures = [
        'wizard_builder_data',
    ]

    @classmethod
    def setUpClass(cls):
        settings.SITE_ID = 1
        super().setUpClass()

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
        form = response.context['form']
        self.assertEqual(
            form.data,
            self.data,
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
        self.client.post(self.choice_url, self.data)
        response = self.client.get(self.review_url)
        form_data = response.context['form_data']
        self.assertIn(
            {'food options': ['sugar']},
            form_data,
        )
