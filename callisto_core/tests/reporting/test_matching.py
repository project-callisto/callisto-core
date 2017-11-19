import json

from callisto_core.tests.utils.api import CustomNotificationApi
from callisto_core.utils.api import MatchingApi
from mock import call, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .. import test_base
from ...delivery.models import MatchReport
from .base import MatchSetup

User = get_user_model()


class MatchPropertyTest(MatchSetup):

    def test_running_matching_sets_report_seen(self):
        self.create_match(self.user1, 'test1', alert=False)
        self.create_match(self.user2, 'test2', alert=False)
        self.assert_matches_not_seen()
        MatchingApi.find_matches('test1')
        self.assert_matches_seen()


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
        self.passphrase = 'user 1 secret'
        self.client.login(username="test1", password="test")
        self.client_post_report_creation()
        # we pass in the default arg to client_post_matching_enter
        # just to make it totally clear that the same identifier
        # is being input twice
        self.client_post_matching_enter('https://www.facebook.com/callistoorg')

        self.passphrase = 'user 2 secret'
        self.client.login(username="tset22", password="test")
        self.client_post_report_creation()
        self.client_post_matching_enter('https://www.facebook.com/callistoorg')

        self.assert_matches_found_true()


class MatchAlertingTest(MatchSetup):

    def test_existing_match_not_retriggered_by_same_reporter(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        matches = self.create_match(self.user2, 'test1')
        self.assertFalse(matches)

    def test_triggers_new_matches_only(self, mock_process):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        matches = self.create_match(self.user3, 'test2')
        self.assertFalse(matches)


class MatchNotificationTest(MatchSetup):

    def test_basic_email_case(self):
        with patch.object(CustomNotificationApi, 'log_action') as api_logging:
            self.create_match(self.user1, 'test1')
            self.assertEqual(api_logging.call_count, 0)
            self.create_match(self.user2, 'test1')
            self.assert_matches_found_true()
            # 2 emails for the 2 users
            # 1 email for the reporting authority
            self.assertEqual(api_logging.call_count, 3)

    def test_multiple_email_case(self):
        with patch.object(CustomNotificationApi, 'log_action') as api_logging:
            self.create_match(self.user1, 'test1')  # 0
            self.create_match(self.user2, 'test1')  # 3 emails
            self.create_match(self.user3, 'test1')  # 7 emails
            self.create_match(self.user4, 'test1')  # 12 emails
            self.assert_matches_found_true()
            self.assertNotEqual(api_logging.call_count, 7)  # old behavior
            self.assertEqual(api_logging.call_count, 12)  # new behavior

    def test_users_are_deduplicated(self):
        with patch.object(CustomNotificationApi, 'log_action') as api_logging:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user1, 'test1')
            self.assertFalse(api_logging.called)
            self.create_match(self.user2, 'test1')
            self.assert_matches_found_true()
            self.assertEqual(api_logging.call_count, 3)

    def test_does_notify_on_reported_reports(self):
        with patch.object(CustomNotificationApi, 'log_action') as api_logging:
            self.create_match(self.user1, 'test1')
            match_report = self.create_match(self.user2, 'test1', alert=False)
            match_report.report.submitted_to_school = timezone.now()
            match_report.report.save()
            MatchingApi.find_matches('test1')
            self.assertNotEqual(api_logging.call_count, 2)  # old behavior
            self.assertEqual(api_logging.call_count, 3)  # new behavior
