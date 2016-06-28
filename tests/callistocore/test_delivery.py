from io import BytesIO

import PyPDF2

from django.contrib.auth import get_user_model
from django.core import mail

from callisto.delivery.models import EmailNotification, Report
from callisto.delivery.report_delivery import (
    PDFFullReport, PDFMatchReport, SentFullReport, SentMatchReport,
)
from .test_matching import MatchTest

User = get_user_model()


class ReportDeliveryTest(MatchTest):

    def setUp(self):
        super(ReportDeliveryTest, self).setUp()
        self.user = self.user1
        self.decrypted_report = """[
    { "answer": "test answer",
      "id": 1,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "answer to 2nd question",
      "id": 2,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]"""
        self.report = Report(owner=self.user)
        self.report.encrypt_report(self.decrypted_report, "a key a key a key")
        self.report.save()

    def test_pdf_full_report_is_generated(self):
        report = PDFFullReport(self.report, self.decrypted_report)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Submitted by: dummy", pdfReader.getPage(0).extractText())
        self.assertIn("test answer", pdfReader.getPage(1).extractText())
        self.assertIn("answer to 2nd question", pdfReader.getPage(1).extractText())

    def test_submission_to_school(self):
        EmailNotification.objects.create(name='report_delivery', subject="test delivery", body="test body")
        report = PDFFullReport(self.report, self.decrypted_report)
        report.send_report_to_school()
        sent_report_id = SentFullReport.objects.latest('id').get_report_id()
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.attachments[0][0], 'report_%s.pdf.gpg' % sent_report_id)

    # TODO: test encryption of submitted report email

    def test_pdf_match_report_is_generated(self):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        report = PDFMatchReport([match1, match2])
        output = report.generate_match_report(report_id=1)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Intended for: Title IX Coordinator Tatiana Nine", pdfReader.getPage(0).extractText())
        self.assertIn("Submitted by: dummy", pdfReader.getPage(0).extractText())
        self.assertIn("Submitted by: ymmud", pdfReader.getPage(0).extractText())

    def test_matches_to_school(self):
        EmailNotification.objects.create(name='match_delivery', subject="test match delivery", body="test match body")
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        report = PDFMatchReport([match1, match2])
        report.send_matching_report_to_school()
        sent_report_id = SentMatchReport.objects.latest('id').get_report_id()
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.attachments[0][0], 'report_%s.pdf.gpg' % sent_report_id)

    def test_user_identifier(self):
        user_with_email = User.objects.create_user(username="email_dummy", password="dummy", email="test@example.com")
        report = Report(owner=user_with_email)
        report.encrypt_report(self.decrypted_report, "a key a key a key")
        report.save()
        pdf_report = PDFFullReport(report, self.decrypted_report)
        output = pdf_report.generate_pdf_report(recipient=None, report_id=None)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        self.assertIn("Submitted by: test@example.com", pdfReader.getPage(0).extractText())
