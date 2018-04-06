from io import BytesIO

import PyPDF2

from callisto_core.tests import test_base
from callisto_core.reporting.report_delivery import report_as_pdf, PDFUserReviewReport

# TODO: generate mock_report_data in wizard builder
mock_report_data = [
    {'food options': ['vegetables', 'apples: red']},
    {'eat it now???': ['catte']},
    {'do androids dream of electric sheep?': ['awdad']},
    {'whats on the radios?': ['guitar']},
]


class UserReviewPDFTest(
    test_base.ReportFlowHelper,
):

    def test_title(self):
        pdf = PDFUserReviewReport.generate({})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertIn(
            PDFUserReviewReport.title,
            pdf_reader.getPage(0).extractText(),
        )

    def test_random_content_not_present(self):
        pdf = PDFUserReviewReport.generate({})
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))
        self.assertNotIn(
            'aowdbaef aieuf aef rv a7fv isfv srifv ivf if7va7evada11111',
            pdf_reader.getPage(0).extractText(),
        )


class ReportPDFTest(
    test_base.ReportFlowHelper,
):

    def test_report_pdf(self):
        self.client_post_report_creation()
        pdf = report_as_pdf(
            report=self.report,
            data=mock_report_data,
            recipient=None,
        )
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))

        self.assertIn(
            'Title IX Coordinator',
            pdf_reader.getPage(0).extractText())
        self.assertIn(
            "Reported by: testing_12",
            pdf_reader.getPage(1).extractText())
        self.assertIn('food options', pdf_reader.getPage(1).extractText())
        self.assertIn('vegetables', pdf_reader.getPage(1).extractText())
        self.assertIn('apples: red', pdf_reader.getPage(1).extractText())
        self.assertIn('eat it now???', pdf_reader.getPage(1).extractText())
