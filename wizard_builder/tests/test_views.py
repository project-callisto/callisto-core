from unittest import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.conf import settings

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
        step = 1
        url = reverse('wizard_update', kwargs={'step': step})
        data = {'question_2': 'aloe ipsum speakerbox'}
        patch = mock.patch.object(
            view_helpers.StorageHelper,
            'add_data_to_storage',
        )
        with patch as storage_mock:
            self.client.post(url, data)
        storage_data = {step: data}
        storage_mock.assert_has_calls([mock.call(storage_data)])
