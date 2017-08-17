from callisto_core.delivery.models import (
    MatchReport, Report, SentFullReport, SentMatchReport,
)

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from .models import LegacyMatchReportData, LegacyReportData

User = get_user_model()


class ReportModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="dummy", password="dummy")

    def test_reports_have_owners(self):
        report = Report()
        report.owner = self.user
        report.save()
        self.assertIn(report, self.user .report_set.all())

    # need to at minimum save which fields were displayed
    def test_cannot_save_empty_reports(self):
        report = Report(owner=self.user, encrypted=b'')
        with self.assertRaises(ValidationError):
            report.save()
            report.full_clean()

    def test_report_owner_is_not_optional(self):
        report = Report(encrypted=b'a report')
        with self.assertRaises(IntegrityError):
            report.save()
            report.full_clean()

    def test_report_ordering(self):
        report1 = Report.objects.create(owner=self.user, encrypted=b'first report')
        report2 = Report.objects.create(owner=self.user, encrypted=b'2 report')
        report3 = Report.objects.create(owner=self.user, encrypted=b'report #3')
        self.assertEqual(
            list(Report.objects.all()),
            [report3, report2, report1]
        )

    def test_can_encrypt_report(self):
        report = Report(owner=self.user)
        report.encrypt_report(
            "this text should be encrypted",
            'this is my key',
        )
        self.assertIsNotNone(report.encode_prefix)
        self.assertNotEqual(report.encode_prefix, '')
        self.assertIsNotNone(report.encrypted)
        self.assertTrue(len(report.encrypted) > 0)

    def test_can_decrypt_report(self):
        report = Report(owner=self.user)
        report.encrypt_report(
            "this text should be encrypted, yes it should by golly!",
            'this is my key',
        )
        report.save()
        saved_report = Report.objects.first()
        self.assertEqual(saved_report.decrypted_report('this is my key'),
                         "this text should be encrypted, yes it should by golly!")

    def test_can_decrypt_old_reports(self):
        legacy_report = LegacyReportData()
        legacy_report.encrypt_report("this text should be encrypted otherwise bad things", key='this is my key')
        report = Report(owner=self.user, encrypted=legacy_report.encrypted, salt=legacy_report.salt)
        report.save()
        saved_report = Report.objects.first()
        self.assertEqual(saved_report.decrypted_report('this is my key'),
                         "this text should be encrypted otherwise bad things")

    def test_no_times_by_default(self):
        report = Report(owner=self.user)
        report.encrypt_report("test report", "key")
        report.save()
        self.assertIsNone(Report.objects.first().last_edited)
        self.assertIsNone(Report.objects.first().submitted_to_school)
        self.assertIsNone(Report.objects.first().entered_into_matching)

    def test_can_withdraw_from_matching(self):
        report = Report(owner=self.user)
        report.encrypt_report("test report", "key")
        report.save()
        MatchReport.objects.create(report=report, contact_email='test@example.com', identifier='dummy')
        self.assertIsNotNone(Report.objects.first().entered_into_matching)
        report.match_found = True
        report.save()
        report.withdraw_from_matching()
        report.save()
        self.assertIsNone(Report.objects.first().entered_into_matching)
        self.assertFalse(Report.objects.first().match_found)


class MatchReportTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="dummy", password="dummy")
        self.report = Report(owner=self.user)
        self.report.encrypt_report("test report", "key")
        self.report.save()
        match_report = MatchReport(report=self.report, identifier='dummy')
        match_report.encrypt_match_report("test match report", match_report.identifier)
        match_report.save()

    def test_entered_into_matching_property_is_set(self):
        self.assertIsNotNone(Report.objects.first().entered_into_matching)

    def test_entered_into_matching_is_blank_before_entering_into_matching(self):
        report = Report(owner=self.user)
        report.encrypt_report("test non-matching report", "key")
        report.save()
        self.assertIsNone(Report.objects.get(pk=report.id).entered_into_matching)

    def test_can_encrypt_match_report(self):
        saved_match_report = MatchReport.objects.first()
        self.assertIsNotNone(saved_match_report.encode_prefix)
        self.assertNotEqual(saved_match_report.encode_prefix, '')
        self.assertIsNotNone(saved_match_report.encrypted)
        self.assertTrue(len(saved_match_report.encrypted) > 0)

    def test_can_decrypt_match_report(self):
        saved_match_report = MatchReport.objects.first()
        self.assertEqual(saved_match_report.get_match('dummy'), "test match report")

    def test_can_decrypt_old_match_report(self):
        legacy_match_report = LegacyMatchReportData()
        legacy_match_report.encrypt_match_report("test legacy match report", "dumbo")

        legacy_report = LegacyReportData()
        legacy_report.encrypt_report("this text should be encrypted otherwise bad things", key='this is my key')
        report = Report(owner=self.user, encrypted=legacy_report.encrypted, salt=legacy_report.salt)
        report.save()

        new_match_report = MatchReport(report=report, encrypted=legacy_match_report.encrypted,
                                       salt=legacy_match_report.salt, identifier="dumbo")
        new_match_report.save()
        self.assertEqual(new_match_report.get_match("dumbo"), "test legacy match report")


class SentReportTest(TestCase):

    def test_id_format_works(self):
        sent_full_report = SentFullReport.objects.create()
        sent_full_report_id = sent_full_report.get_report_id()
        sent_match_report = SentMatchReport.objects.create()
        sent_match_report_id = sent_match_report.get_report_id()
        self.assertNotEqual(sent_match_report_id, sent_full_report_id)
        self.assertTrue(sent_full_report_id.endswith('-1'))
        self.assertTrue(sent_match_report_id.endswith('-0'))


class DeleteReportTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="dummy", password="dummy")
        self.report = Report(owner=self.user)
        self.report.encrypt_report("test report", "key")
        self.report.save()

    def test_can_delete_report(self):
        self.assertEqual(Report.objects.count(), 1)
        self.report.delete()
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(User.objects.first(), self.user)

    def test_deleted_report_deletes_match_report(self):
        match_report = MatchReport(report=self.report, identifier='dummy')
        match_report.encrypt_match_report("test match report", match_report.identifier)
        match_report.save()
        self.assertEqual(MatchReport.objects.count(), 1)
        self.report.delete()
        self.assertEqual(MatchReport.objects.count(), 0)

    def test_deleted_report_doesnt_delete_sent_report(self):
        sent_report = SentFullReport.objects.create(report=self.report)
        self.assertIsNotNone(self.report.sentfullreport_set.first())
        self.assertEqual(self.report, SentFullReport.objects.first().report)
        self.report.delete()
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(SentFullReport.objects.first(), sent_report)

    def test_deleted_report_doesnt_delete_sent_match_report(self):
        match_report = MatchReport(report=self.report, identifier='dummy')
        match_report.encrypt_match_report("test match report", 'dummy')
        match_report.save()
        user2 = User.objects.create_user(username="dummy2", password="dummy")
        report2 = Report(owner=user2)
        report2.encrypt_report("test report 2", "key")
        report2.save()
        match_report2 = MatchReport(report=report2, identifier='dummy')
        match_report2.encrypt_match_report("test match report 2", 'dummy')
        match_report2.save()
        sent_match_report = SentMatchReport.objects.create()
        sent_match_report.reports.add(match_report, match_report2)
        self.report.match_found = True
        self.report.save()
        report2.match_found = True
        report2.save()
        self.assertIsNotNone(match_report.sentmatchreport_set.first())
        self.assertIsNotNone(match_report2.sentmatchreport_set.first())
        self.assertEqual(match_report, SentMatchReport.objects.first().reports.all()[0])
        self.assertEqual(match_report2, SentMatchReport.objects.first().reports.all()[1])
        self.report.delete()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(MatchReport.objects.count(), 1)
        self.assertEqual(SentMatchReport.objects.first(), sent_match_report)
        self.assertEqual(SentMatchReport.objects.first().reports.count(), 1)
        self.assertEqual(SentMatchReport.objects.first().reports.first(), match_report2)
        self.assertTrue(Report.objects.first().match_found)
        report2.delete()
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(SentMatchReport.objects.first(), sent_match_report)
