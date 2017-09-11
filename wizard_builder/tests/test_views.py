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

    def test_storage_receives_post_data(self):
        step = '1'
        url = reverse('wizard_update', kwargs={'step': step})
        data = {'question_2': 'aloe ipsum speakerbox'}
        storage_data = {step: data}
        self.client.post(url, data)
        self.assertEqual(
            self.client.session['data'],
            storage_data,
        )
