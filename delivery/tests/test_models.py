from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import MatchReport, Report, SentFullReport, SentMatchReport

User = get_user_model()

class ReportModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="dummy", password="dummy")

    def test_reports_have_owners(self):
        report = Report()
        report.owner = self.user
        report.save()
        self.assertIn(report, self.user .report_set.all())

    #need to at minimum save which fields were displayed
    def test_cannot_save_empty_reports(self):
        report = Report(owner=self.user , encrypted=b'')
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

    def test_get_absolute_url(self):
        report = Report.objects.create(encrypted=b'some report', owner=self.user)
        self.assertEqual(report.get_absolute_url(), '/reports/view/%d/' % (report.id,))

    def test_can_encrypt_report(self):
        report = Report(owner=self.user)
        report.encrypt_report("this text should be encrypted", key='this is my key')
        report.save()
        saved_report = Report.objects.first()
        self.assertIsNotNone(saved_report.salt)
        self.assertNotEqual(saved_report.salt, '')
        self.assertIsNotNone(saved_report.encrypted)
        self.assertTrue(len(saved_report.encrypted) > 0)

    def test_can_decrypt_report(self):
        report = Report(owner=self.user)
        report.encrypt_report("this text should be encrypted, yes it should by golly!", key='this is my key')
        report.save()
        saved_report = Report.objects.first()
        self.assertEqual(saved_report.decrypted_report('this is my key'), "this text should be encrypted, yes it should by golly!")

    def test_no_times_by_default(self):
        report = Report(owner=self.user)
        report.encrypt_report("test report", "key")
        report.save()
        self.assertIsNone(Report.objects.first().last_edited)
        self.assertIsNone(Report.objects.first().submitted_to_school)
        self.assertIsNone(Report.objects.first().entered_into_matching)

    def test_edit_sets_edited_time(self):
        report = Report(owner=self.user)
        report.encrypt_report("test report", "key")
        report.save()
        report.encrypt_report("a different report", "key")
        report.save()
        self.assertIsNotNone(Report.objects.first().last_edited)

    def test_can_withdraw_from_matching(self):
        report = Report(owner=self.user)
        report.encrypt_report("test report", "key")
        report.save()
        MatchReport.objects.create(report = report, contact_phone='phone',
                                   contact_email='test@example.com', identifier='dummy')
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

    def test_entered_into_matching_property_is_set(self):
        report = Report(owner = self.user)
        report.encrypt_report("test report", "key")
        report.save()
        MatchReport.objects.create(report = report, contact_phone='phone',
                                   contact_email='test@example.com', identifier='dummy')
        self.assertIsNotNone(Report.objects.first().entered_into_matching)

    def test_entered_into_matching_is_blank_before_entering_into_matching(self):
        report = Report(owner = self.user)
        report.encrypt_report("test report", "key")
        report.save()
        self.assertIsNone(Report.objects.first().entered_into_matching)

class SentReportTest(TestCase):
    def test_id_format_works_on_full(self):
        sent_report = SentFullReport.objects.create()
        self.assertEqual(sent_report.get_report_id(), '000-00001-1')

    def test_id_format_works_on_match(self):
        sent_report = SentMatchReport.objects.create()
        self.assertEqual(sent_report.get_report_id(), '000-00002-0')
