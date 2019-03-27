import json
from unittest import skip

from django_migration_testcase import MigrationTest
from mock import ANY, patch

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from callisto_core.delivery import encryption
from callisto_core.reporting.report_delivery import MatchReportContent
from callisto_core.utils.api import MatchingApi

from .models import _legacy_decrypt_report, _legacy_encrypt_report

User = get_user_model()


class MatchReportMigrationTest(MigrationTest):

    app_name = 'delivery'
    before = '0003_allow_deletion_of_identifier'
    after = '0007_add_argon2_with_rolling_upgrades'

    @skip('migration already run')
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
        MatchReport.objects.create(
            report=report,
            identifier=identifier,
            contact_phone=phone,
            contact_voicemail=voicemail,
            contact_name=user_name,
            contact_email=email,
            name=perp_name,
            seen=True)
        self.assertEqual(MatchReport.objects.count(), 1)

        self.run_migration()

        MatchReport = self.get_model_after('MatchReport')
        self.assertEqual(MatchReport.objects.count(), 1)
        match_report = MatchReport.objects.first()
        self.assertEqual(match_report.identifier, None)
        decrypted_report = json.loads(
            _legacy_decrypt_report(
                match_report.salt,
                identifier,
                encryption.unpepper(
                    match_report.encrypted)))
        self.assertEqual(decrypted_report['identifier'], identifier)
        self.assertEqual(decrypted_report['perp_name'], perp_name)
        self.assertEqual(decrypted_report['phone'], phone)
        self.assertEqual(decrypted_report['voicemail'], voicemail)
        self.assertEqual(decrypted_report['contact_name'], user_name)
        self.assertEqual(decrypted_report['email'], email)
        self.assertEqual(decrypted_report['notes'], None)

    @skip('migration already run')
    @patch('callisto.delivery.reporting.CallistoMatching.process_new_matches')
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
        MatchReport.objects.create(
            report=report,
            identifier=identifier,
            contact_phone=phone,
            contact_name=user_name,
            contact_email=email,
            name=perp_name,
            seen=True)
        self.assertEqual(MatchReport.objects.count(), 1)

        self.run_migration()

        MatchReport = self.get_model_after('MatchReport')
        MatchReport.objects.first()
        user2 = User.objects.create_user(username="dummy2", password="dummy")
        Report = self.get_model_after('Report')
        report2 = Report(owner_id=user2.pk)
        report2.save()
        report_content = MatchReportContent(
            identifier='test_identifier',
            perp_name='Perperick',
            contact_name='Rita',
            email='email1@example.com',
            phone='555-555-1212')
        salt = get_random_string()
        encrypted_report = encryption.pepper(
            _legacy_encrypt_report(
                salt, identifier, json.dumps(
                    report_content.__dict__)))
        match_report = MatchReport.objects.create(
            report=report2,
            identifier=identifier,
            encrypted=encrypted_report,
            salt=salt)
        MatchingApi.find_matches('test_identifier')
        # have to use ANY because objects in migration tests are faked
        mock_process.assert_called_once_with([ANY, ANY], 'test_identifier')


class MultipleRecipientMigrationTest(MigrationTest):

    app_name = 'delivery'
    before = '0008_make_salt_nullable'
    after = '0009_to_address_to_textfield'

    @skip('migration already run')
    def test_recipient_data_is_migrated(self):

        user = User.objects.create_user(username="dummy", password="dummy")
        Report = self.get_model_before('Report')
        report = Report(owner_id=user.pk)
        report.save()
        SentFullReport = self.get_model_before('SentFullReport')
        sent_report = SentFullReport.objects.create(
            report_id=report.pk, to_address="test@example.com")
        sent_report.save()
        self.assertEqual(SentFullReport.objects.count(), 1)

        self.run_migration()

        SentFullReport = self.get_model_after('SentFullReport')
        self.assertEqual(SentFullReport.objects.count(), 1)
        sent_report = SentFullReport.objects.first()
        self.assertEqual(sent_report.to_address, 'test@example.com')
