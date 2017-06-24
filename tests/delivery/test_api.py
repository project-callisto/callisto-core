from mock import patch

from django.test import TestCase, override_settings

from callisto.delivery.api import DeliveryApi
from callisto.delivery.matching import MatchingApi


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.mock_argument_1 = 'mock argument 1'
        self.mock_argument_2 = 'mock argument 2'

    @patch('callisto.notification.api.NotificationApi.send_report_to_authority')
    def test_default_notification_api_call(self, mock_process):
        DeliveryApi().send_report_to_authority(self.mock_argument_1, self.mock_argument_2)
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.ExtendedCustomNotificationApi')
    @patch('tests.callistocore.forms.ExtendedCustomNotificationApi.send_report_to_authority')
    def test_overridden_notification_api_call(self, mock_process):
        DeliveryApi().send_report_to_authority(self.mock_argument_1, self.mock_argument_2, 'cats')
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2, 'cats')

    def test_abritrary_method_names_can_be_used(self):
        self.assertEqual(
            DeliveryApi().send_claws_to_scratch_couch(),
            None,
        )

    @patch('callisto.delivery.matching.CallistoMatching.find_matches')
    def test_default_matching_api_call(self, mock_process):
        MatchingApi().find_matches()
        mock_process.assert_called_once_with()

    @override_settings(CALLISTO_MATCHING_API='tests.callistocore.forms.CustomMatchingApi')
    @patch('tests.callistocore.forms.CustomMatchingApi.run_matching')
    def test_overridden_matching_api_call(self, mock_process):
        MatchingApi().run_matching(self.mock_argument_1)
        mock_process.assert_called_once_with(self.mock_argument_1)
