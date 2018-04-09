from unittest.mock import call, patch

from callisto_core.tests.utils.api import CustomNotificationApi
from callisto_core.tests.test_base import ReportFlowHelper as ReportFlowTestCase

from callisto_core.reporting.views import ReportingConfirmationView

class ConfirmationViewTest(
    ReportFlowTestCase,
):

    def test_default_calls(self):
        with patch.object(CustomNotificationApi, 'send_email') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        self.assertEqual(api_logging.call_count, 3)

    def test_demo_mode_calls(self):
        with patch.object(CustomNotificationApi, 'send_email') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        self.assertEqual(api_logging.call_count, 2)
