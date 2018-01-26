from unittest import skip
from unittest.mock import call, patch

from django.urls import reverse

from callisto_core.delivery.forms import ReportAccessForm
from callisto_core.delivery.models import MatchReport, SentFullReport
from callisto_core.notification.models import EmailNotification
from callisto_core.reporting import view_partials
from callisto_core.reporting.forms import ConfirmationForm
from callisto_core.tests import test_base
from callisto_core.tests.utils.api import CustomNotificationApi


class ReportingHelper(test_base.ReportFlowHelper):

    def setUp(self):
        super().setUp()
        self.client_post_report_creation()

    def recovers_from_no_passphrase(self):
        self.client_clear_passphrase()
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

    def test_recovers_from_no_passphrase(self):
        self.recovers_from_no_passphrase()


class MatchingHelper(ReportingHelper):

    def does_not_create_a_full_report(self):
        self.assertEqual(SentFullReport.objects.count(), 0)
        self.request()
        self.assertEqual(SentFullReport.objects.count(), 0)


class MatchingViewTest(MatchingHelper):

    def test_multiple_email_copies_resolved(self):
        email = EmailNotification.objects.create(name='match_confirmation')
        email.sites.add(1)
        self.client_post_matching_enter()

    def test_multiple_emails_not_sent(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_matching_enter()

        self.assertEqual(
            api_logging.call_args_list.count(
                call(notification_name='match_confirmation')
            ), 1
        )

    def test_emails_not_sent_when_no_key(self):
        self.client_clear_passphrase()
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_matching_enter()

        self.assertEqual(api_logging.call_count, 0)


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

    def test_recovers_from_no_passphrase(self):
        self.recovers_from_no_passphrase()


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

    def test_recovers_from_no_passphrase(self):
        self.recovers_from_no_passphrase()


class ConfirmationViewTest(ReportingHelper):

    def request(self):
        return self.client_post_reporting_end_step()

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
