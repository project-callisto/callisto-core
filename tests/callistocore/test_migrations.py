import json

from django_migration_testcase import MigrationTest
from mock import ANY, patch

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from callisto.delivery.matching import find_matches
from callisto.delivery.models import (
    _decrypt_report, _encrypt_report, _pepper, _unpepper,
)
from callisto.delivery.report_delivery import (
    MatchReportContent, PDFMatchReport,
)

User = get_user_model()

class MatchReportMigrationTest(MigrationTest):

    app_name = 'delivery'
    before = '0003_allow_deletion_of_identifier'
    after = '0005_delete_encrypted_fields_from_match_report'

    def test_fields_are_encrypted(self):

        user = User.objects.create_user(username="dummy", password="dummy")
        Report = self.get_model_before('Report')
        report = Report(owner_id=user.pk)
        report.save()
        MatchReport = self.get_model_before('MatchReport')
        identifier = "test_identifier"
        phone = "555-1212"
        voicemail = "Please don't leave a voicemail"
        user_name = "Maggie"
        email = "migration@example.com"
        perp_name = "Perp"
        MatchReport.objects.create(report=report, identifier=identifier, contact_phone=phone,
                                   contact_voicemail=voicemail, contact_name=user_name, contact_email=email,
                                   name=perp_name, seen=True)
        self.assertEqual(MatchReport.objects.count(), 1)

        self.run_migration()

        MatchReport = self.get_model_after('MatchReport')
        self.assertEqual(MatchReport.objects.count(), 1)
        match_report = MatchReport.objects.first()
        self.assertEqual(match_report.identifier, None)
        decrypted_report = json.loads(_decrypt_report(match_report.salt, identifier, _unpepper(match_report.encrypted)))
        self.assertEqual(decrypted_report['identifier'], identifier)
        self.assertEqual(decrypted_report['perp_name'], perp_name)
        self.assertEqual(decrypted_report['phone'], phone)
        self.assertEqual(decrypted_report['voicemail'], voicemail)
        self.assertEqual(decrypted_report['contact_name'], user_name)
        self.assertEqual(decrypted_report['email'], email)
        self.assertEqual(decrypted_report['notes'], None)

    @patch('callisto.delivery.matching.process_new_matches')
    def test_matches_after_encryption(self, mock_process):

        user1 = User.objects.create_user(username="dummy1", password="dummy")
        Report = self.get_model_before('Report')
        report = Report(owner_id=user1.pk)
        report.save()
        MatchReport = self.get_model_before('MatchReport')
        identifier = "test_identifier"
        phone = "555-1212"
        user_name = "Maggie"
        email = "migration@example.com"
        perp_name = "Perp"
        MatchReport.objects.create(report=report, identifier=identifier, contact_phone=phone,
                                   contact_name=user_name, contact_email=email,
                                   name=perp_name, seen=True)
        self.assertEqual(MatchReport.objects.count(), 1)

        self.run_migration()

        MatchReport = self.get_model_after('MatchReport')
        MatchReport.objects.first()
        user2 = User.objects.create_user(username="dummy2", password="dummy")
        Report = self.get_model_after('Report')
        report2 = Report(owner_id=user2.pk)
        report2.save()
        report_content = MatchReportContent(identifier='test_identifier', perp_name='Perperick', contact_name='Rita',
                                            email='email1@example.com', phone='555-555-1212')
        salt = get_random_string()
        encrypted_report = _pepper(_encrypt_report(salt, identifier, json.dumps(report_content.__dict__)))
        MatchReport.objects.create(report=report2, identifier=identifier, encrypted=encrypted_report,
                                   salt=salt)
        find_matches([identifier])
        # have to use ANY because objects in migration tests are faked
        mock_process.assert_called_once_with([ANY, ANY], 'test_identifier', PDFMatchReport)
