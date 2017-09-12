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
        self.url = reverse('wizard_update', kwargs={'step': self.step})

    def test_storage_receives_post_data(self):
        self.client.post(self.url, self.data)
        self.assertEqual(
            self.client.session[view_helpers.StorageHelper.session_data_key],
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
