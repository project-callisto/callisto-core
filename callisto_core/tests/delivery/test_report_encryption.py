import json

import gnupg

from django.test import TestCase, override_settings

from callisto_core.delivery.models import RecordHistorical, Report
from callisto_core.tests.evaluation import test_keypair
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)


class ReportEncryptionTest(
    ReportFlowTestCase,
):

    def test_not_authorized_without_owner(self):
        self.report = Report.objects.create()
        response = self.client_post_report_pdf_view(skip_assertions=True)
        self.assertEqual(response.status_code, 403)

    def test_can_decrypt_without_setup(self):
        self.report = Report.objects.create(
            owner=self.user,
        )
        self.client_post_report_pdf_view()


class ReportGPGEncryptionTest(
    TestCase,
):

    @override_settings(CALLISTO_EVAL_PUBLIC_KEY=test_keypair.public_test_key)
    def test_gpg_decryption(self):
        report = Report()
        report._store_for_callisto_decryption({'rawr': 'cats'})

        gpg = gnupg.GPG()
        gpg.import_keys(test_keypair.private_test_key)
        gpg_data = gpg.decrypt(report.encrypted_eval)
        data = json.loads(gpg_data.data)

        self.assertEqual(data, {'rawr': 'cats'})


class HistoricalSavingTest(ReportFlowTestCase):

    def test_multiple_historical_records_saved(self):
        self.client_post_report_creation()
        self.client_post_answer_second_page_question()
        self.assertGreater(RecordHistorical.objects.count(), 1)

    def test_most_recent_record_historical_saves_with_record(self):
        self.client_post_report_creation()

        self.assertEqual(
            RecordHistorical.objects.first().encrypted_eval,
            Report.objects.first().encrypted_eval,
        )

        self.client_post_answer_second_page_question()

        self.assertNotEqual(
            RecordHistorical.objects.first().encrypted_eval,
            Report.objects.first().encrypted_eval,
        )
        self.assertEqual(
            RecordHistorical.objects.last().encrypted_eval,
            Report.objects.first().encrypted_eval,
        )


@override_settings(CALLISTO_EVAL_PUBLIC_KEY=test_keypair.public_test_key)
class AnswerEncryptionTest(ReportFlowTestCase):

    def _get_answers(self, record):
        gpg = gnupg.GPG()
        gpg.import_keys(test_keypair.private_test_key)
        gpg_data = gpg.decrypt(record.encrypted_eval)
        data = json.loads(gpg_data.data)
        try:
            return data['data']
        except BaseException:
            return {}

    def test_eval_pops_some_answers(self):
        '''
        when a question is answered that skips eval
        assert that no eval row contains all report answers
        '''
        self.client_post_report_creation()
        self.client_post_answer_second_page_question()
        report_answers = self.report.decrypt_record(self.passphrase)['data']

        self.assertTrue(report_answers)
        for record in RecordHistorical.objects.filter(record=self.report):
            eval_answers = self._get_answers(record)
            self.assertLess(len(eval_answers), len(report_answers))

    def test_eval_doesnt_pop_skipped_answers(self):
        '''
        when no questions are answered that skip eval
        assert that at least on eval row contains all report answers
        '''
        self.client_post_report_creation()
        self.client_post_answer_question()
        report_answers = self.report.decrypt_record(self.passphrase)['data']

        self.assertTrue(len(report_answers))
        for record in RecordHistorical.objects.filter(record=self.report):
            eval_answers = self._get_answers(record)
            if len(eval_answers) == len(report_answers):
                break
        else:
            raise AssertionError(
                'No RecordHistorical.encrypted_eval with accurate size')
