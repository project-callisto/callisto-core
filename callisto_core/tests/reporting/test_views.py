from callisto_core.delivery.models import MatchReport

from .. import test_base


class MatchingTest(test_base.ReportFlowHelper):

    def test_enter_into_matching(self):
        self.assertEqual(MatchReport.objects.count(), 0)
        self.client_post_report_creation()
        self.client_post_enter_matching()
        self.assertEqual(MatchReport.objects.count(), 1)


class ReportingTest(test_base.ReportFlowHelper):
    pass
