from callisto_core.utils.api import MatchingApi, NotificationApi
from mock import patch

from django.test import TestCase, override_settings


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.mock_argument_1 = 'mock argument 1'
        self.mock_argument_2 = 'mock argument 2'

    @patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_report_to_authority')
    def test_default_notification_api_call(self, mock_process):
        NotificationApi.send_report_to_authority(self.mock_argument_1, self.mock_argument_2)
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.ExtendedCustomNotificationApi')
    @patch('tests.callistocore.forms.ExtendedCustomNotificationApi.send_report_to_authority')
    def test_overridden_notification_api_call(self, mock_process):
        NotificationApi.send_report_to_authority(self.mock_argument_1, self.mock_argument_2, 'cats')
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2, 'cats')

    def test_abritrary_method_names_can_be_used(self):
        self.assertEqual(
            NotificationApi.send_claws_to_scratch_couch(),
            None,
        )

    @patch('callisto_core.delivery.api.CallistoCoreMatchingApi.find_matches')
    def test_default_matching_api_call(self, mock_process):
        MatchingApi.find_matches()
        mock_process.assert_called_once_with()

    @override_settings(CALLISTO_MATCHING_API='tests.callistocore.forms.CustomMatchingApi')
    @patch('tests.callistocore.forms.CustomMatchingApi.run_matching')
    def test_overridden_matching_api_call(self, mock_process):
        MatchingApi.run_matching(self.mock_argument_1)
        mock_process.assert_called_once_with(self.mock_argument_1)
