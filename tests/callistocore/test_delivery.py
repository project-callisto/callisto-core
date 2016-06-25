from datetime import datetime
from io import BytesIO

import PyPDF2
from mock import patch, call

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from callisto.delivery.matching import find_matches
from callisto.delivery.models import EmailNotification, MatchReport, Report
from callisto.delivery.report_delivery import (
    PDFFullReport, PDFMatchReport, SentFullReport, SentMatchReport,
)

User = get_user_model()


class MatchTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="dummy", password="dummy")
        self.user2 = User.objects.create_user(username="ymmud", password="dummy")

    def create_match(self, user, identifier):
        report = Report(owner = user)
        report.encrypt_report("test report 1", "key")
        report.save()
        return MatchReport.objects.create(report=report, contact_phone='phone',
                                          contact_email='test@example.com', identifier=identifier)


@patch('callisto.delivery.matching.process_new_matches')
class MatchDiscoveryTest(MatchTest):

    def test_two_matching_reports_match(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        find_matches()
        mock_process.assert_called_once_with([match1, match2])
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)

    def test_non_matching_reports_dont_match(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy1')
        find_matches()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)

    def test_matches_only_triggered_by_different_people(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy1')
        match3 = self.create_match(self.user2, 'dummy1')
        find_matches()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)
        self.assertFalse(match3.report.match_found)

    def test_existing_match_not_retriggered_by_same_reporter(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        find_matches()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        match3 = self.create_match(self.user2, 'dummy')
        find_matches()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)
        self.assertTrue(match3.report.match_found)

    def test_triggers_new_matches_only(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        find_matches()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="dummy")
        self.create_match(user3, 'dummy1')
        find_matches()
        self.assertFalse(mock_process.called)
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)

    def test_three_way_match(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy1')
        find_matches()
        self.assertFalse(mock_process.called)
        user3 = User.objects.create_user(username="yumdm", password="dummy")
        match3 = self.create_match(user3, 'dummy1')
        user4 = User.objects.create_user(username="mmudy", password="dummy")
        match4 = self.create_match(user4, 'dummy1')
        find_matches()
        mock_process.assert_called_once_with([match2, match3, match4])
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        match3.report.refresh_from_db()
        match4.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertTrue(match2.report.match_found)
        self.assertTrue(match3.report.match_found)
        self.assertTrue(match4.report.match_found)

    def test_existing_match_still_triggers_on_new(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        find_matches()
        self.assertTrue(mock_process.called)
        mock_process.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="dummy")
        match3 = self.create_match(user3, 'dummy')
        find_matches()
        mock_process.assert_called_once_with([match1, match2, match3])

    def test_error_during_processing_means_match_not_seen(self, mock_process):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        mock_process.side_effect = [Exception('Boom!'), ()]
        try:
            find_matches()
        except:
            pass
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertFalse(match1.report.match_found)
        self.assertFalse(match2.report.match_found)
        mock_process.reset_mock()
        find_matches()
        mock_process.assert_called_once_with([match1, match2])
        match1.report.refresh_from_db()
        match2.report.refresh_from_db()
        self.assertTrue(match1.report.match_found)
        self.assertTrue(match2.report.match_found)


@patch('callisto.delivery.matching.send_notification_email')
@patch('callisto.delivery.report_delivery.PDFMatchReport.send_email_to_coordinator')
class MatchNotificationTest(MatchTest):
    def setUp(self):
        self.user1 = User.objects.create_user(username="dummy", password="dummy")
        self.user2 = User.objects.create_user(username="ymmud", password="dummy")

    def test_both_new_matches_sent_emails(self, mock_send_to_school, mock_send_email):
        report1 = self.create_match(self.user1, 'dummy')
        report2 = self.create_match(self.user2, 'dummy')
        find_matches()
        calls = [call(self.user1, report1), call(self.user2, report2)]
        mock_send_email.assert_has_calls(calls)
        self.assertEqual(mock_send_email.call_count, 2)

    def test_only_new_matches_sent_emails(self, mock_send_to_school, mock_send_email):
        self.create_match(self.user1, 'dummy')
        self.create_match(self.user2, 'dummy')
        find_matches()
        self.assertTrue(mock_send_email.called)
        mock_send_email.reset_mock()
        user3 = User.objects.create_user(username="yumdm", password="dummy")
        report3 = self.create_match(user3, 'dummy')
        find_matches()
        mock_send_email.assert_called_once_with(user3, report3)

    def test_users_are_deduplicated(self, mock_send_to_school, mock_send_email):
        report1 = self.create_match(self.user1, 'dummy')
        self.create_match(self.user1, 'dummy')
        find_matches()
        self.assertFalse(mock_send_email.called)
        report3 = self.create_match(self.user2, 'dummy')
        find_matches()
        calls = [call(self.user1, report1), call(self.user2, report3)]
        mock_send_email.assert_has_calls(calls)
        self.assertEqual(mock_send_email.call_count, 2)

    def test_doesnt_notify_on_reported_reports(self, mock_send_to_school, mock_send_email):
        report1 = self.create_match(self.user1, 'dummy')
        report2 = self.create_match(self.user2, 'dummy')
        report2.report.submitted_to_school = datetime.now()
        report2.report.save()
        find_matches()
        mock_send_email.assert_called_once_with(self.user1, report1)


class ReportDeliveryTest(MatchTest):

    def setUp(self):
        super(ReportDeliveryTest, self).setUp()
        self.user = self.user1
        self.decrypted_report = """[
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
        self.report = Report(owner=self.user)
        self.report.encrypt_report(self.decrypted_report, "a key a key a key")
        self.report.save()

    def test_pdf_full_report_is_generated(self):
        report = PDFFullReport(self.report, self.decrypted_report)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Submitted by: dummy", pdfReader.getPage(0).extractText())
        self.assertIn("test answer", pdfReader.getPage(1).extractText())
        self.assertIn("answer to 2nd question", pdfReader.getPage(1).extractText())

    def test_submission_to_school(self):
        EmailNotification.objects.create(name='report_delivery', subject="test delivery", body="test body")
        report = PDFFullReport(self.report, self.decrypted_report)
        report.send_report_to_school()
        sent_report_id = SentFullReport.objects.latest('id').get_report_id()
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.attachments[0][0], 'report_%s.pdf.gpg' % sent_report_id)

    # TODO: test encryption of submitted report email

    def test_pdf_match_report_is_generated(self):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        report = PDFMatchReport([match1, match2])
        output = report.generate_match_report(report_id=1)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Intended for: Title IX Coordinator Tatiana Nine", pdfReader.getPage(0).extractText())
        self.assertIn("Submitted by: dummy", pdfReader.getPage(0).extractText())
        self.assertIn("Submitted by: ymmud", pdfReader.getPage(0).extractText())

    def test_matches_to_school(self):
        EmailNotification.objects.create(name='match_delivery', subject="test match delivery", body="test match body")
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        report = PDFMatchReport([match1, match2])
        report.send_matching_report_to_school()
        sent_report_id = SentMatchReport.objects.latest('id').get_report_id()
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.attachments[0][0], 'report_%s.pdf.gpg' % sent_report_id)

    def test_user_identifier(self):
        user_with_email = User.objects.create_user(username="email_dummy", password="dummy", email="test@example.com")
        report = Report(owner=user_with_email)
        report.encrypt_report(self.decrypted_report, "a key a key a key")
        report.save()
        pdf_report = PDFFullReport(report, self.decrypted_report)
        output = pdf_report.generate_pdf_report(recipient=None, report_id=None)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Submitted by: test@example.com", pdfReader.getPage(0).extractText())
