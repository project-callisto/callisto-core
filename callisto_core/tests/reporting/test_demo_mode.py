from unittest import skip
from unittest.mock import call, patch

from django.contrib.sites.models import Site

from callisto_core.reporting.views import ReportingConfirmationView
from callisto_core.tests.test_base import ReportFlowHelper as ReportFlowTestCase
from callisto_core.tests.utils.api import CustomNotificationApi
from callisto_core.utils.sites import TempSiteID


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class DemoModeNotificationSubjectTest(ReportFlowTestCase):
    def test_default(self):
        with patch.object(CustomNotificationApi, "_logging") as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        api_logging.assert_has_calls([call(subject="report_delivery")], any_order=True)

    def test_demo_mode(self):
        Site.objects.get_or_create(id=4)

        with TempSiteID(4), patch.object(
            CustomNotificationApi, "_logging"
        ) as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        api_logging.assert_has_calls(
            [call(DEMO_MODE=True), call(subject="[DEMO] report_delivery")],
            any_order=True,
        )


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class DemoModeNotificationNameTest(ReportFlowTestCase):
    def test_default(self):
        with patch.object(CustomNotificationApi, "_logging") as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        api_logging.assert_has_calls(
            [
                call(notification_name="submit_confirmation"),
                call(notification_name="report_delivery"),
                call(
                    notification_name=ReportingConfirmationView.admin_email_template_name
                ),
            ],
            any_order=True,
        )

    def test_demo_mode(self):
        Site.objects.get_or_create(id=4)

        with TempSiteID(4), patch.object(
            CustomNotificationApi, "_logging"
        ) as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        api_logging.assert_has_calls(
            [
                call(notification_name="submit_confirmation"),
                call(notification_name="report_delivery"),
            ],
            any_order=True,
        )


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class DemoModeNotificationCallCountTest(ReportFlowTestCase):
    def test_default(self):
        with patch.object(CustomNotificationApi, "send_email") as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        self.assertEqual(api_logging.call_count, 3)

    def test_demo_mode(self):
        Site.objects.get_or_create(id=4)

        with TempSiteID(4), patch.object(
            CustomNotificationApi, "send_email"
        ) as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        self.assertEqual(api_logging.call_count, 2)
