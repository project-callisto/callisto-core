from mock import ANY, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from callisto.delivery.api import DeliveryApi
from callisto.delivery.matching import MatchingApi
from callisto.delivery.models import Report, SentFullReport
from callisto.notification.models import EmailNotification

User = get_user_model()


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

    def test_invalid_notification_calls_raise_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            DeliveryApi().send_claws_to_scratch_couch(self.mock_argument_1, self.mock_argument_2)

    @patch('callisto.delivery.matching.CallistoMatching.find_matches')
    def test_default_matching_api_call(self, mock_process):
        MatchingApi().find_matches()
        mock_process.assert_called_once_with()

    @override_settings(CALLISTO_MATCHING_API='tests.callistocore.forms.CustomMatchingApi')
    @patch('tests.callistocore.forms.CustomMatchingApi.run_matching')
    def test_overridden_matching_api_call(self, mock_process):
        MatchingApi().run_matching(self.mock_argument_1)
        mock_process.assert_called_once_with(self.mock_argument_1)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.CustomBackendNotificationApi')
    @patch('django.core.mail.backends.dummy.EmailBackend.send_messages')
    def test_custom_email_backend(self, mock_backend):
        decrypted_report = """[
    { "answer": "test answer",
      "id": 1,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "answer to 2nd question",
      "id": 2,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]"""
        report = Report(owner=User.objects.create_user(username="dummy", password="dummy"))
        report.encrypt_report(decrypted_report, "a key a key a key")
        report.save()
        sent_full_report = SentFullReport.objects.create(report=report, to_address="whatever")
        EmailNotification.objects.create(
            name='report_delivery',
            subject="test delivery",
            body="test body",
        ).sites.add(1)
        DeliveryApi().send_report_to_authority(sent_full_report, decrypted_report, 1)
        mock_backend.assert_called_once_with(ANY)
