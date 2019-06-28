import json
from unittest import skip

import gnupg

from django.test import override_settings

from callisto_core.delivery.models import Report
from callisto_core.evaluation.models import EvalRow
from callisto_core.tests.evaluation import test_keypair
from callisto_core.tests.test_base import ReportFlowHelper as ReportFlowTestCase


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class EvalViewTest(ReportFlowTestCase):
    def test_some_eval_rows_created(self):
        self.assertFalse(EvalRow.objects.count())
        self.client_post_report_creation()
        self.assertTrue(EvalRow.objects.count())

    def test_eval_rows_have_record_attached(self):
        self.assertFalse(EvalRow.objects.count())
        self.client_post_report_creation()
        self.assertTrue(EvalRow.objects.filter(record=self.report).count())

    def test_action_create(self):
        self.assertFalse(EvalRow.objects.filter(action="CREATE").count())
        self.client_post_report_creation()
        self.assertTrue(EvalRow.objects.filter(action="CREATE").count())

    def test_action_edit(self):
        self.assertFalse(EvalRow.objects.filter(action="EDIT").count())
        self.client_post_report_creation()
        self.client_post_answer_question()
        self.assertTrue(EvalRow.objects.filter(action="EDIT").count())

    def test_action_review(self):
        self.assertFalse(EvalRow.objects.filter(action="REVIEW").count())
        self.client_post_report_creation()
        self.client_post_answer_question()
        self.assertFalse(EvalRow.objects.filter(action="REVIEW").count())
        self.client_get_review()
        self.assertTrue(EvalRow.objects.filter(action="REVIEW").count())

    def test_action_delete(self):
        self.assertFalse(EvalRow.objects.filter(action="DELETE").count())
        self.client_post_report_creation()
        self.client_post_report_delete()
        self.assertTrue(EvalRow.objects.filter(action="DELETE").count())

    def test_action_pdf_view(self):
        self.assertFalse(EvalRow.objects.filter(action="VIEW_PDF").count())
        self.client_post_report_creation()
        self.client_post_report_pdf_view()
        self.assertTrue(EvalRow.objects.filter(action="VIEW_PDF").count())

    def test_action_contact_prep(self):
        self.assertFalse(
            EvalRow.objects.filter(action="CONTACT_INFO_PREPERATION").count()
        )
        self.client_post_report_creation()
        self.client_post_report_prep()
        self.assertTrue(
            EvalRow.objects.filter(action="CONTACT_INFO_PREPERATION").count()
        )

    def test_action_matching_enter(self):
        self.assertFalse(
            EvalRow.objects.filter(action="ENTER_MATCHING_REQUIRED").count()
        )
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.assertTrue(
            EvalRow.objects.filter(action="ENTER_MATCHING_REQUIRED").count()
        )

    def test_action_matching_withdraw(self):
        self.assertFalse(EvalRow.objects.filter(action="MATCHING_WITHDRAW").count())
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.client_post_matching_withdraw()
        self.assertTrue(EvalRow.objects.filter(action="MATCHING_WITHDRAW").count())

    def test_action_reporting(self):
        self.assertFalse(
            EvalRow.objects.filter(action="DIRECT_REPORTING_FINAL_CONFIRMATION").count()
        )
        self.client_post_report_creation()
        self.client_post_reporting_end_step()
        self.assertTrue(
            EvalRow.objects.filter(action="DIRECT_REPORTING_FINAL_CONFIRMATION").count()
        )
