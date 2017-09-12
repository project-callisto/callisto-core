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
        self.storage_data = {self.step: self.data}

    def test_storage_receives_post_data(self):
        url = reverse('wizard_update', kwargs={'step': self.step})
        self.client.post(url, self.data)
        self.assertEqual(
            self.client.session['data'],
            self.storage_data,
        )
