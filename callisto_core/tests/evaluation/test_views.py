import json

import gnupg

from django.test import override_settings

from callisto_core.evaluation.models import EvalRow
from callisto_core.tests.evaluation import test_keypair
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)


class EvalViewTest(ReportFlowTestCase):

    def test_some_eval_rows_created(self):
        self.assertFalse(EvalRow.objects.count())
        self.client_post_report_creation()
        self.assertTrue(EvalRow.objects.count())

    def test_action_create(self):
        self.assertFalse(EvalRow.objects.filter(action='CREATE').count())
        self.client_post_report_creation()
        self.assertTrue(EvalRow.objects.filter(action='CREATE').count())

    def test_action_edit(self):
        self.assertFalse(EvalRow.objects.filter(action='EDIT').count())
        self.client_post_report_creation()
        self.client_post_answer_question()
        self.assertTrue(EvalRow.objects.filter(action='EDIT').count())

    def test_action_review(self):
        self.assertFalse(EvalRow.objects.filter(action='REVIEW').count())
        self.client_post_report_creation()
        self.client_post_answer_question()
        self.assertFalse(EvalRow.objects.filter(action='REVIEW').count())
        self.client_get_review()
        self.assertTrue(EvalRow.objects.filter(action='REVIEW').count())

    def test_action_delete(self):
        self.assertFalse(EvalRow.objects.filter(action='DELETE').count())
        self.client_post_report_creation()
        self.client_post_report_delete()
        self.assertTrue(EvalRow.objects.filter(action='DELETE').count())

    def test_action_pdf_view(self):
        self.assertFalse(EvalRow.objects.filter(action='VIEW_PDF').count())
        self.client_post_report_creation()
        self.client_post_report_pdf_view()
        self.assertTrue(EvalRow.objects.filter(action='VIEW_PDF').count())

    def test_action_contact_prep(self):
        self.assertFalse(EvalRow.objects.filter(action='CONTACT_PREP').count())
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.assertTrue(EvalRow.objects.filter(action='CONTACT_PREP').count())

    def test_action_matching_enter(self):
        self.assertFalse(
            EvalRow.objects.filter(action='ENTER_MATCHING').count())
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.assertTrue(
            EvalRow.objects.filter(action='ENTER_MATCHING').count())

    def test_action_matching_withdraw(self):
        self.assertFalse(
            EvalRow.objects.filter(action='MATCHING_WITHDRAW').count())
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.client_post_matching_withdraw()
        self.assertTrue(
            EvalRow.objects.filter(action='MATCHING_WITHDRAW').count())

    def test_action_reporting(self):
        self.assertFalse(EvalRow.objects.filter(action='REPORTING').count())
        self.client_post_report_creation()
        self.client_post_reporting_confirmation()
        self.assertTrue(EvalRow.objects.filter(action='REPORTING').count())


@override_settings(CALLISTO_EVAL_PUBLIC_KEY=test_keypair.public_test_key)
class AnswerEncryptionTest(ReportFlowTestCase):

    def _get_answers(self, evalrow):
        gpg = gnupg.GPG()
        gpg.import_keys(test_keypair.private_test_key)
        gpg_data = gpg.decrypt(evalrow.record_encrypted)
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
        report_answers = self.report.decrypted_report(self.passphrase)['data']
        for evalrow in EvalRow.objects.all():
            eval_answers = self._get_answers(evalrow)
            self.assertLess(len(eval_answers), len(report_answers))

    def test_eval_doesnt_pop_skipped_answers(self):
        '''
        when no questions are answered that skip eval
        assert that at least on eval row contains all report answers
        '''
        self.client_post_report_creation()
        self.client_post_answer_question()
        report_answers = self.report.decrypted_report(self.passphrase)['data']
        for evalrow in EvalRow.objects.all():
            eval_answers = self._get_answers(evalrow)
            if len(eval_answers) == len(report_answers):
                break
        else:
            raise AssertionError('No EvalRow with accurate size')
