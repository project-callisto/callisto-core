from unittest import skip
from unittest.mock import call, patch

from callisto_core.delivery.forms import ReportAccessForm
from callisto_core.delivery.models import MatchReport, SentFullReport
from callisto_core.reporting import view_partials
from callisto_core.reporting.forms import ConfirmationForm

from .. import test_base
from ..utils.api import CustomNotificationApi


class ReportingHelper(test_base.ReportFlowHelper):

    def setUp(self):
        super().setUp()
        self.client_post_report_creation()

    def recovers_from_no_secret_key(self):
        self.client_clear_secret_key()
        response = self.request()
        self.assertIsInstance(response.context['form'], ReportAccessForm)


class SubmissionViewTest(ReportingHelper):

    def setUp(self):
        super().setUp()

    def request(self):
        return self.client_post_report_prep()

    def test_submission_template_used(self):
        response = self.request()
        self.assertTemplateUsed(
            response,
            'callisto_core/reporting/submission.html',
        )

    def test_recovers_from_no_secret_key(self):
        self.recovers_from_no_secret_key()


class MatchingHelper(ReportingHelper):

    def does_not_create_a_full_report(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.request()
        self.assertEqual(SentFullReport.objects.count(), 0)


class MatchingOptionalViewTest(MatchingHelper):

    def request(self):
        return self.client_post_matching_enter_empty()

    def test_match_report_not_created(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.request()
        self.assertEqual(MatchReport.objects.count(), 0)

    def test_empty_form_advances_page(self):
        response = self.request()
        self.assertIsInstance(response.context['form'], ConfirmationForm)

    def test_sends_no_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.request()

        self.assertEqual(api_logging.call_count, 0)

    def test_does_not_create_a_full_report(self):
        self.does_not_create_a_full_report()

    def test_recovers_from_no_secret_key(self):
        self.recovers_from_no_secret_key()


class MatchingRequiredViewTest(MatchingHelper):

    def request(self):
        return self.client_post_matching_enter()

    def test_match_report_created(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.request()
        self.assertEqual(MatchReport.objects.count(), 1)

    def test_sends_match_confirmation_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.request()

        api_logging.assert_has_calls([
            call(notification_name='match_confirmation'),
        ], any_order=True)

    def test_does_not_create_a_full_report(self):
        self.does_not_create_a_full_report()

    def test_recovers_from_no_secret_key(self):
        self.recovers_from_no_secret_key()


class ConfirmationViewTest(ReportingHelper):

    def request(self):
        return self.client_post_reporting_confirmation()

    def test_creates_a_full_report(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.request()
        self.assertEqual(SentFullReport.objects.count(), 1)

    def test_sends_emails(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.request()

        api_logging.assert_has_calls([
            call(notification_name='submit_confirmation'),
            call(notification_name='report_delivery'),
        ], any_order=True)

    def test_accepts_secret_key_in_form(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_clear_secret_key()
            self.request()

        api_logging.assert_has_calls([
            call(notification_name='submit_confirmation'),
            call(notification_name='report_delivery'),
        ], any_order=True)
