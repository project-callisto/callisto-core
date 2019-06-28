from io import BytesIO
from unittest import skip

import PyPDF2
from mock import patch

from callisto_core.delivery.models import MatchReport
from callisto_core.notification.management.commands.user_review_email import (
    UserReviewCommandBackend,
)
from callisto_core.reporting.report_delivery import PDFUserReviewReport, report_as_pdf
from callisto_core.tests import test_base
from callisto_core.tests.reporting.base import MatchSetup
from callisto_core.tests.utils.api import CustomNotificationApi

# TODO: generate mock_report_data in wizard builder
mock_report_data = [
    {"food options": ["vegetables", "apples: red"]},
    {"eat it now???": ["catte"]},
    {"do androids dream of electric sheep?": ["awdad"]},
    {"whats on the radios?": ["guitar"]},
]


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class UserReviewPDFTest(test_base.ReportFlowHelper):
    def test_text_present(self):
        pdf = PDFUserReviewReport.generate({})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertTrue(pdf_reader.getPage(0).extractText())

    def test_title(self):
        pdf = PDFUserReviewReport.generate({})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(PDFUserReviewReport.title, pdf_reader.getPage(0).extractText())

    def test_random_content_not_present(self):
        pdf = PDFUserReviewReport.generate({})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertNotIn(
            "aowdbaef aieuf aef rv a7fv isfv srifv ivf if7va7evada11111",
            pdf_reader.getPage(0).extractText(),
        )

    def test_report_page(self):
        self.client_post_report_creation()
        pdf = PDFUserReviewReport.generate({"reports": [self.report]})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn("Report", pdf_reader.getPage(1).extractText())

    def test_report_contact_info_present(self):
        self.client_post_report_creation()
        self.client_post_report_prep()
        pdf = PDFUserReviewReport.generate({"reports": [self.report]})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(self.report_contact_email, pdf_reader.getPage(1).extractText())
        self.assertIn(self.report_contact_phone, pdf_reader.getPage(1).extractText())

    def test_two_reports(self):
        self.client_post_report_creation()
        self.client_post_report_prep()
        pdf = PDFUserReviewReport.generate({"reports": [self.report, self.report]})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(self.report_contact_email, pdf_reader.getPage(2).extractText())
        self.assertIn(self.report_contact_phone, pdf_reader.getPage(2).extractText())

    def test_output_file(self):
        """
            for when you want to see what the file looks like
            $ open UserReviewPDFTest.pdf
        """
        self.client_post_report_creation()
        self.client_post_report_prep()
        pdf = PDFUserReviewReport.generate({"reports": [self.report, self.report]})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        with open("UserReviewPDFTest.pdf", "wb") as _file:
            dst_pdf = PyPDF2.PdfFileWriter()
            dst_pdf.appendPagesFromReader(pdf_reader)
            dst_pdf.write(_file)


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class MatchingUserReviewPDFTest(MatchSetup):
    def test_title(self):
        matching_id = "test1a08daw awd7awgd 1213123"
        self.create_match(self.user1, matching_id)
        self.create_match(self.user2, matching_id)
        pdf = PDFUserReviewReport.generate({"matches": MatchReport.objects.all()})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(PDFUserReviewReport.title, pdf_reader.getPage(0).extractText())

    def test_matching_id_not_present(self):
        matching_id = "test1a08daw awd7awgd 1213123"
        self.create_match(self.user1, matching_id)
        self.create_match(self.user2, matching_id)
        pdf = PDFUserReviewReport.generate({"matches": MatchReport.objects.all()})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertNotIn(matching_id, pdf_reader.getPage(1).extractText())
        self.assertNotIn(matching_id, pdf_reader.getPage(2).extractText())

    def test_contact_info_present(self):
        matching_id = "test1a08daw awd7awgd 1213123"
        contact_phone = "555-555-5555"
        self.create_match(self.user1, matching_id)
        self.create_match(self.user2, matching_id)
        self.most_recent_report.contact_phone = contact_phone
        self.most_recent_report.save()
        pdf = PDFUserReviewReport.generate({"matches": MatchReport.objects.all()})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(contact_phone, pdf_reader.getPage(2).extractText())

    def test_output_file(self):
        """
            for when you want to see what the file looks like
            $ open MatchingUserReviewPDFTest.pdf
        """
        matching_id = "test1a08daw awd7awgd 1213123"
        self.create_match(self.user1, matching_id)
        self.create_match(self.user2, matching_id)
        self.most_recent_report.contact_phone = "555-555-5555"
        self.most_recent_report.save()
        pdf = PDFUserReviewReport.generate({"matches": MatchReport.objects.all()})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        with open("MatchingUserReviewPDFTest.pdf", "wb") as _file:
            dst_pdf = PyPDF2.PdfFileWriter()
            dst_pdf.appendPagesFromReader(pdf_reader)
            dst_pdf.write(_file)


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ManagementCommandTest(MatchSetup):
    def test_action_logged(self):
        matching_id = "test1a08daw awd7awgd 1213123"
        self.create_match(self.user1, matching_id)
        self.create_match(self.user2, matching_id)
        with patch.object(CustomNotificationApi, "log_action") as api_logging:
            UserReviewCommandBackend().send_user_review_email()
            self.assertEqual(api_logging.call_count, 1)


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ReportPDFTest(test_base.ReportFlowHelper):
    def test_report_pdf(self):
        self.client_post_report_creation()
        pdf = report_as_pdf(report=self.report, data=mock_report_data, recipient=None)
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))

        self.assertIn("Title IX Coordinator", pdf_reader.getPage(0).extractText())
        self.assertIn("Reported by: testing_12", pdf_reader.getPage(1).extractText())
        self.assertIn("food options", pdf_reader.getPage(1).extractText())
        self.assertIn("vegetables", pdf_reader.getPage(1).extractText())
        self.assertIn("apples: red", pdf_reader.getPage(1).extractText())
        self.assertIn("eat it now???", pdf_reader.getPage(1).extractText())
