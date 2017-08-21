from mock import patch

from django.test import TestCase, override_settings

from ...utils.api import NotificationApi


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.mock_argument_1 = 'mock argument 1'
        self.mock_argument_2 = 'mock argument 2'

    @patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_report_to_authority')
    def test_default_notification_api_call(self, mock_process):
        NotificationApi.send_report_to_authority(
            self.mock_argument_1, self.mock_argument_2)
        mock_process.assert_called_once_with(
            self.mock_argument_1, self.mock_argument_2)

    @override_settings(
        CALLISTO_NOTIFICATION_API='callisto_core.tests.callistocore.forms.ExtendedCustomNotificationApi')
    @patch('callisto_core.tests.callistocore.forms.ExtendedCustomNotificationApi.send_report_to_authority')
    def test_overridden_notification_api_call(self, mock_process):
        NotificationApi.send_report_to_authority(
            self.mock_argument_1, self.mock_argument_2, 'cats')
        mock_process.assert_called_once_with(
            self.mock_argument_1, self.mock_argument_2, 'cats')

    def test_abritrary_method_names_can_be_used(self):
        self.assertEqual(
            NotificationApi.send_claws_to_scratch_couch(),
            None,
        )
