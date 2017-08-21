import json

from mock import call, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from ...delivery.models import MatchReport
from ...utils.api import MatchingApi
from .base import MatchSetup

User = get_user_model()


@override_settings(
    CALLISTO_MATCHING_API='callisto_core.tests.utils.api.CustomMatchingApi')
@patch('callisto_core.tests.utils.api.CustomMatchingApi.process_new_matches')
class MatchDiscoveryTest(MatchSetup):

    def test_running_matching_sets_report_seen(self, mock_process):
        self.create_match(self.user1, 'test')
        self.create_match(self.user2, 'test2')
        for report in MatchReport.objects.all():
            self.assertFalse(report.seen)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertTrue(report.seen)

    def test_running_matching_erases_identifier(self, mock_process):
        self.create_match(self.user1, 'test')
        self.create_match(self.user2, 'test2')
        for report in MatchReport.objects.all():
            self.assertIsNotNone(report.identifier)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertIsNone(report.identifier)

    def test_two_matching_reports_match(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        mock_process.assert_called_once_with([match1, match2], 'test')
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)

    def test_non_matching_reports_dont_match(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test1')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)

    def test_matches_only_triggered_by_different_people(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test1')
        match3 = self.create_match(self.user2, 'test1')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)
        self.assertFalse(match3.report.match_found)

    def test_existing_match_not_retriggered_by_same_reporter(
            self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        match3 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)
        self.assertTrue(match3.report.match_found)

    def test_triggers_new_matches_only(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="test")
        self.create_match(user3, 'test1')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)

    def test_three_way_match(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test1')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        user3 = User.objects.create_user(username="yumdm", password="test")
        match3 = self.create_match(user3, 'test1')
        user4 = User.objects.create_user(username="mmudy", password="test")
        match4 = self.create_match(user4, 'test1')
        MatchingApi.run_matching()
        mock_process.assert_called_once_with(
            [match2, match3, match4], 'test1')
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        match4.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertTrue(match2.report.match_found)
        self.assertTrue(match3.report.match_found)
        self.assertTrue(match4.report.match_found)

    def test_multiple_match(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        user3 = User.objects.create_user(username="yumdm", password="test")
        match3 = self.create_match(user3, 'test')
        MatchingApi.run_matching()
        mock_process.assert_called_once_with([match1, match2, match3], 'test')
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)
        self.assertTrue(match3.report.match_found)

    def test_existing_match_still_triggers_on_new(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="test")
        match3 = self.create_match(user3, 'test')
        MatchingApi.run_matching()
        mock_process.assert_called_once_with([match1, match2, match3], 'test')

    def test_double_match(self, mock_process):
        match1 = self.create_match(self.user1, 'test1')
        match2 = self.create_match(self.user2, 'test2')
        MatchingApi.run_matching()
        self.assertFalse(mock_process.called)
        user3 = User.objects.create_user(username="yumdm", password="test")
        match3 = self.create_match(user3, 'test1')
        match4 = self.create_match(user3, 'test2')
        MatchingApi.run_matching()
        call1 = call([match1, match3], 'test1')
        call2 = call([match2, match4], 'test2')
        mock_process.assert_has_calls([call1, call2])

    def test_error_during_processing_means_match_not_seen(self, mock_process):
        match1 = self.create_match(self.user1, 'test')
        match2 = self.create_match(self.user2, 'test')
        mock_process.side_effect = [Exception('Boom!'), ()]
        try:
            MatchingApi.run_matching()
        except BaseException:
            pass
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)
        mock_process.reset_mock()
        MatchingApi.run_matching()
        mock_process.assert_called_once_with([match1, match2], 'test')
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)


@patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_match_notification')
@override_settings(
    CALLISTO_NOTIFICATION_API='callisto_core.tests.callistocore.forms.SendDisabledNotificationApi')
class MatchNotificationTest(MatchSetup):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="test", password="test")
        self.user2 = User.objects.create_user(
            username="ymmud", password="test")

    def test_both_new_matches_sent_emails(self, mock_send_email):
        report1 = self.create_match(self.user1, 'test')
        report2 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        calls = [call(self.user1, report1), call(self.user2, report2)]
        mock_send_email.assert_has_calls(calls)
        self.assertEqual(mock_send_email.call_count, 2)

    def test_multiple_match_sends_emails_to_all(self, mock_send_email):
        report1 = self.create_match(self.user1, 'test')
        report2 = self.create_match(self.user2, 'test')
        user3 = User.objects.create_user(username="yumdm", password="test")
        report3 = self.create_match(user3, 'test')
        MatchingApi.run_matching()
        calls = [
            call(
                self.user1, report1), call(
                self.user2, report2), call(
                user3, report3)]
        mock_send_email.assert_has_calls(calls)
        self.assertEqual(mock_send_email.call_count, 3)

    def test_only_new_matches_sent_emails(self, mock_send_email):
        self.create_match(self.user1, 'test')
        self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        self.assertTrue(mock_send_email.called)
        mock_send_email.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="test")
        report3 = self.create_match(user3, 'test')
        MatchingApi.run_matching()
        mock_send_email.assert_called_once_with(user3, report3)

    def test_users_are_deduplicated(self, mock_send_email):
        report1 = self.create_match(self.user1, 'test')
        self.create_match(self.user1, 'test')
        MatchingApi.run_matching()
        self.assertFalse(mock_send_email.called)
        report3 = self.create_match(self.user2, 'test')
        MatchingApi.run_matching()
        calls = [call(self.user1, report1), call(self.user2, report3)]
        mock_send_email.assert_has_calls(calls)
        self.assertEqual(mock_send_email.call_count, 2)

    def test_doesnt_notify_on_reported_reports(self, mock_send_email):
        report1 = self.create_match(self.user1, 'test')
        report2 = self.create_match(self.user2, 'test')
        report2.report.submitted_to_school = timezone.now()
        report2.report.save()
        MatchingApi.run_matching()
        mock_send_email.assert_called_once_with(self.user1, report1)
