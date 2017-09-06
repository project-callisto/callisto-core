from io import BytesIO

import PyPDF2

from wizard_builder import view_helpers as wizard_builer_helpers

from .. import test_base
from ...reporting import report_delivery

# TODO: generate mock_report_data in wizard builder
mock_report_data = [
    {'food options': ['vegetables', 'apples: red']},
    {'do androids dream of electric sheep?': ['awdad']},
    {'whats on the radios?': ['guitar']},
]


class ReportPDFTest(test_base.ReportFlowHelper):

    def test_report_pdf(self):
        self.client_post_report_creation()
        pdf = report_delivery.report_as_pdf(
            report=self.report,
            data=mock_report_data,
            recipient=None,
        )
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf))

        self.assertIn(
            "Reported by: testing_12",
            pdf_reader.getPage(0).extractText())
        self.assertIn('food options', pdf_reader.getPage(0).extractText())
        self.assertIn('vegetables', pdf_reader.getPage(0).extractText())
        self.assertIn('apples: red', pdf_reader.getPage(0).extractText())
        self.assertIn(
            wizard_builer_helpers.SerializedDataHelper.not_answered_text,
            pdf_reader.getPage(0).extractText(),
        )
