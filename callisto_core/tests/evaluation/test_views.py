from callisto_core.evaluation.models import EvalRow
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
