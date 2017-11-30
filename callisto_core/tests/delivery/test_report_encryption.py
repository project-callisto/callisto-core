from django.test import TestCase

from callisto_core.delivery.models import Report

from callisto_core.tests.test_base import ReportFlowHelper


class ReportEncryptionTest(
    ReportFlowHelper,
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
