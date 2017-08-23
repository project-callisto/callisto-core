from unittest.mock import call, patch

from callisto_core.delivery.models import MatchReport
from callisto_core.reporting.forms import SubmitToMatchingForm

from .. import test_base
from ..utils.api import CustomNotificationApi


class BaseReportingTest(test_base.ReportFlowHelper):

    def test_respects_email_confirmation_false(self):
        pass


class MatchingTest(test_base.ReportFlowHelper):

    def test_match_report_created(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_enter_matching()
        self.assertEqual(MatchReport.objects.count(), 1)

    def test_secret_key_required(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_clear_secret_key()
        self.client_post_enter_matching()
        self.assertEqual(MatchReport.objects.count(), 0)

    def test_match_submission_does_not_submit_a_report(self):
        pass

    def test_sends_match_confirmation_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_enter_matching()

        api_logging.assert_has_calls([
            call(response_status=200),
            call(body='matching confirm email'),
        ], any_order=True)


class ReportingTest(test_base.ReportFlowHelper):

    def test_post_to_confirmation_sends_report_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting()

        api_logging.assert_has_calls([
            call(response_status=200),
            call(body='reporting confirm email'),
        ], any_order=True)
