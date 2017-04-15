from mock import patch
from tests.callistocore.forms import CustomNotificationApi

from django.test import TestCase, override_settings

from callisto.delivery.api import DeliveryNotificationApi


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.mock_argument_1 = 'mock argument 1'
        self.mock_argument_2 = 'mock argument 2'

    @patch('callisto.notification.api.NotificationApi.send_report_to_school')
    def test_default_api_call(self, mock_process):
        DeliveryNotificationApi().send_report_to_school(self.mock_argument_1, self.mock_argument_2)
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.CustomNotificationApi')
    @patch('callisto.notification.api.NotificationApi.send_report_to_school')
    def test_overriden_api_call(self, mock_process):
        DeliveryNotificationApi().send_report_to_school(self.mock_argument_1, self.mock_argument_2)
        mock_process.assert_called_once_with(self.mock_argument_1, self.mock_argument_2)
        self.assertEqual(DeliveryNotificationApi().from_email, CustomNotificationApi.from_email)
