from callisto_core.evaluation.models import EvalRow
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)


class EvalViewTest(ReportFlowTestCase):

    def test_some_eval_rows_created(self):
        self.assertEqual(EvalRow.objects.count(), 0)
        self.client_post_report_creation()
        self.assertNotEqual(EvalRow.objects.count(), 0)
