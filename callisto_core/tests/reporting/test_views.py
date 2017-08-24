from unittest.mock import call, patch

from callisto_core.delivery.models import MatchReport, SentFullReport
from callisto_core.reporting.forms import MatchingRequiredForm

from .. import test_base
from ..utils.api import CustomNotificationApi


class MatchingTest(test_base.ReportFlowHelper):

    def test_match_report_created(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.client_post_matching_enter()
        self.assertEqual(MatchReport.objects.count(), 1)

    def test_secret_key_required(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.client_clear_secret_key()
        self.client_post_matching_enter()
        self.assertEqual(MatchReport.objects.count(), 0)

    def test_does_not_create_a_full_report(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.client_post_matching_enter()
        self.assertEqual(SentFullReport.objects.count(), 0)

    def test_sends_match_confirmation_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_report_prep()
            self.client_post_matching_enter()

        api_logging.assert_has_calls([
            call(notification_name='match_confirmation'),
        ], any_order=True)


class ReportingTest(test_base.ReportFlowHelper):

    def test_creates_a_full_report(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.client_post_reporting_confirmation()
        self.assertEqual(SentFullReport.objects.count(), 1)

    def test_secret_key_required(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.client_post_reporting_confirmation()
        self.assertEqual(SentFullReport.objects.count(), 0)

    def test_post_to_confirmation_sends_report_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_report_prep()
            self.client_post_reporting_confirmation()

        api_logging.assert_has_calls([
            call(notification_name='submit_confirmation'),
            call(notification_name='report_delivery'),
        ], any_order=True)
