import json

from mock import call, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .. import test_base
from ...delivery.models import MatchReport
from .base import MatchSetup

from callisto_core.utils.api import MatchingApi
from callisto_core.tests.utils.api import CustomNotificationApi

User = get_user_model()


class MatchPropertyTest(MatchSetup):

    def test_running_matching_sets_report_seen(self):
        self.create_match(self.user1, 'test1', alert=False)
        self.create_match(self.user2, 'test2', alert=False)
        for report in MatchReport.objects.all():
            self.assertFalse(report.seen)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertTrue(report.seen)

    def test_running_matching_erases_identifier(self):
        self.create_match(self.user1, 'test1', alert=False)
        self.create_match(self.user2, 'test2', alert=False)
        for report in MatchReport.objects.all():
            self.assertIsNotNone(report.identifier)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertIsNone(report.identifier)


class MatchDiscoveryTest(MatchSetup):

    def test_two_matching_reports_match(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assert_matches_found_true()

    def test_non_matching_reports_dont_match(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test2')
        self.assert_matches_found_false()

    def test_matches_only_triggered_by_different_people(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user1, 'test1')
        self.assert_matches_found_false()

    def test_multiple_matches(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.create_match(self.user3, 'test1')
        self.create_match(self.user4, 'test1')
        self.assert_matches_found_true()


class MatchIntegratedTest(
    MatchSetup,
    test_base.ReportPostHelper,
):
    fixtures = [
        'wizard_builder_data',
        'callisto_core_notification_data',
    ]

    def test_two_match_post_requests_trigger_matching(self):
        self.secret_key = 'user 1 secret'
        self.client.login(username="test1", password="test")
        self.client_post_report_creation()
        # we pass in the default arg to client_post_matching_enter
        # just to make it totally clear that the same identifier
        # is being input twice
        self.client_post_matching_enter('https://www.facebook.com/callistoorg')

        self.secret_key = 'user 2 secret'
        self.client.login(username="tset22", password="test")
        self.client_post_report_creation()
        self.client_post_matching_enter('https://www.facebook.com/callistoorg')

        self.assert_matches_found_true()


@patch('callisto_core.tests.utils.api.CustomMatchingApi.process_new_matches')
class MatchAlertingTest(MatchSetup):

    def test_existing_match_not_retriggered_by_same_reporter(
            self, mock_process):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assertTrue(mock_process.called)

        mock_process.reset_mock()
        self.create_match(self.user2, 'test1')
        self.assertFalse(mock_process.called)

    def test_error_during_processing_means_match_not_seen(self, mock_process):
        mock_process.side_effect = [Exception('Boom!'), ()]
        try:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user2, 'test1')
        except BaseException:
            pass
        self.assert_matches_found_false()

        mock_process.reset_mock()
        MatchingApi.run_matching()
        self.assert_matches_found_true()

    def test_triggers_new_matches_only(self, mock_process):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assertTrue(mock_process.called)

        mock_process.reset_mock()
        self.create_match(self.user3, 'test2')
        self.assertFalse(mock_process.called)


class MatchNotificationTest(MatchSetup):

    def test_basic_email_case(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user2, 'test1')
            self.assert_matches_found_true()
            self.assertEqual(api_logging.call_count, 2)

    def test_multiple_email_case(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user2, 'test1')
            self.create_match(self.user3, 'test1')
            self.create_match(self.user4, 'test1')
            self.assert_matches_found_true()
            self.assertEqual(api_logging.call_count, 4)

    def test_users_are_deduplicated(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user1, 'test1')
            self.assertFalse(api_logging.called)
            self.create_match(self.user2, 'test1')
            self.assert_matches_found_true()
            self.assertEqual(api_logging.call_count, 2)

    def test_doesnt_notify_on_reported_reports(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.create_match(self.user1, 'test1')
            match_report = self.create_match(self.user2, 'test1', alert=False)
            match_report.report.submitted_to_school = timezone.now()
            match_report.report.save()
            MatchingApi.run_matching()
            self.assertEqual(api_logging.call_count, 1)
