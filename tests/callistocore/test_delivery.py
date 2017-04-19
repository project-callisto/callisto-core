from io import BytesIO

import PyPDF2
import pytz
import six

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from django.utils.timezone import localtime

from callisto.delivery.api import DeliveryApi
from callisto.delivery.models import Report, SentFullReport, SentMatchReport
from callisto.delivery.report_delivery import (
    MatchReportContent, PDFFullReport, PDFMatchReport,
)
from callisto.notification.models import EmailNotification

from .test_matching import MatchTest

User = get_user_model()


class ReportRenderTest(MatchTest):

    def setUp(self):
        super(ReportRenderTest, self).setUp()
        self.user = self.user1
        self.report = Report(owner=self.user)
        self.report.save()

    def test_checkbox_rendered(self):
        checkbox_question = '''[
        {"answer": [0,2,4],
        "id": 1,
        "section": 1,
        "question_text": "A checkbox question?",
        "choices": [{"id": 0, "choice_text": "This is checkbox choice 0"},
        {"id": 1, "choice_text": "This is checkbox choice 1"},
        {"id": 2, "choice_text": "This is checkbox choice 2"},
        {"id": 3, "choice_text": "This is checkbox choice 3"},
        {"id": 4, "choice_text": "This is checkbox choice 4"}],
        "extra": {
        "extra_text": "Extra text for choice 0",
        "answer": "Extra checkbox answer text"
        },
        "type": "Checkbox"
        }
        ]'''
        report = PDFFullReport(self.report, checkbox_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('A checkbox question?', rendered_text)
        for i in range(5):
            if i in [0, 2, 4]:
                # Zapf Dingbats "a23" or "BALLOT X" is encoded as 0x37 or "7"
                regex = '7\\s+This is checkbox choice {}'.format(i)
            else:
                # Zapf Dingbats "a73" or "BALLOT SQUARE" is encoded as 0x6E or "n"
                regex = 'n\\s+This is checkbox choice {}'.format(i)
            six.assertRegex(self, rendered_text, regex)
        self.assertIn('Extra text for choice 0', rendered_text)
        self.assertIn('Extra checkbox answer text', rendered_text)

    def test_date_rendered(self):
        date_question = '''[
        { "answer": "01/01/2016",
        "id": 1,
        "section": 1,
        "question_text": "Date text question?",
        "type": "Date"
        }
        ]'''
        report = PDFFullReport(self.report, date_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Date text question?', rendered_text)
        self.assertIn('01/01/2016', rendered_text)

    def test_date_no_answer_rendered(self):
        date_question = '''[
        { "answer": "",
        "id": 1,
        "section": 1,
        "question_text": "Date text question?",
        "type": "Date"
        }
        ]'''
        report = PDFFullReport(self.report, date_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Date text question?', rendered_text)
        self.assertIn('Not answered', rendered_text)

    def test_empty_formset_rendered(self):
        formset_question = '''[
        { "answers": [],
        "id": 1,
        "section": 1,
        "prompt": "Formset",
        "type": "FormSet"
        }
        ]'''
        report = PDFFullReport(self.report, formset_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()
        self.assertNotIn('Formset 1', rendered_text)
        self.assertIn('Formset', rendered_text)
        self.assertIn('None added', rendered_text)

    def test_single_formset_rendered(self):
        formset_question = '''[
        { "answers": [[
        { "answer": 0,
        "id": 1,
        "section": 1,
        "question_text": "Checkbox question?",
        "choices": [{"id": 0, "choice_text": "This is checkbox choice 0"},
        {"id": 1, "choice_text": "This is checkbox choice 1"},
        {"id": 2, "choice_text": "This is checkbox choice 2"}
        ],
        "extra": {
        "extra_text": "Extra text for choice 0",
        "answer": "Extra checkbox answer text"
        },
        "type": "Checkbox"
        }]
        ],
        "id": 1,
        "section": 1,
        "prompt": "Formset",
        "type": "FormSet"
        }
        ]'''
        report = PDFFullReport(self.report, formset_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()
        self.assertNotIn('Formset 1', rendered_text)
        self.assertIn('Formset', rendered_text)
        self.assertIn('Checkbox question?', rendered_text)
        # Zapf Dingbats "a23" or "BALLOT X" is encoded as 0x37 or "7"
        six.assertRegex(self, rendered_text, '7\\s+This is checkbox choice 0')
        # Zapf Dingbats "a73" or "BALLOT SQUARE" is encoded as 0x6E or "n"
        six.assertRegex(self, rendered_text, 'n\\s+This is checkbox choice 1')
        six.assertRegex(self, rendered_text, 'n\\s+This is checkbox choice 2')
        self.assertIn('Extra text for choice 0', rendered_text)
        self.assertIn('Extra checkbox answer text', rendered_text)

    def test_multiple_formsets_rendered(self):
        formset_question = '''[
        { "answers": [[
        { "answer": "4/16/2016",
        "id": 1,
        "section": 1,
        "question_text": "Date text question?",
        "type": "Date"
        }],
        [
        { "answer": "Multiline\\ntext\\nanswer",
        "id": 1,
        "section": 1,
        "question_text": "Multiline text question?",
        "type": "MultiLineText"
        }]

        ],
        "id": 1,
        "section": 1,
        "prompt": "Formset",
        "type": "FormSet"
        }
        ]'''
        report = PDFFullReport(self.report, formset_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()
        self.assertIn('Formset 1', rendered_text)
        self.assertIn('Date text question?', rendered_text)
        self.assertIn('4/16/2016', rendered_text)
        self.assertIn('Formset 2', rendered_text)
        self.assertIn('Multiline text question?', rendered_text)
        self.assertIn('Multiline\ntext\nanswer', rendered_text)

    def test_multiline_text_rendered(self):
        multiline_question = '''[
        { "answer": "Multiline\\ntext\\nanswer",
        "id": 1,
        "section": 1,
        "question_text": "Multiline text question?",
        "type": "MultiLineText"
        }
        ]'''
        report = PDFFullReport(self.report, multiline_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Multiline text question?', rendered_text)
        self.assertIn('Multiline\ntext\nanswer', rendered_text)

    def test_multiline_text_no_answer_rendered(self):
        multiline_question = '''[
        { "answer": "",
        "id": 1,
        "section": 1,
        "question_text": "Multiline text question?",
        "type": "MultiLineText"
        }
        ]'''
        report = PDFFullReport(self.report, multiline_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Multiline text question?', rendered_text)
        self.assertIn('Not answered', rendered_text)

    def test_radiobutton_rendered(self):
        radio_question = '''[
        {"answer": 0,
        "id": 1,
        "section": 1,
        "question_text": "A radiobutton question?",
        "choices": [
        {"id": 0, "choice_text": "This is radiobutton choice 0"},
        {"id": 1, "choice_text": "This is radiobutton choice 1"},
        {"id": 2, "choice_text": "This is radiobutton choice 2"},
        {"id": 3, "choice_text": "This is radiobutton choice 3"},
        {"id": 4, "choice_text": "This is radiobutton choice 4"}
        ],
        "extra": {
        "extra_text": "Extra text for choice 0",
        "answer": "Extra radiobutton answer text"
        },
        "type": "RadioButton"
        }
        ]'''
        report = PDFFullReport(self.report, radio_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)

        rendered_text = pdf_reader.getPage(1).extractText()
        self.assertIn('A radiobutton question?', rendered_text)
        for i in range(5):
            if i == 0:
                # Zapf Dingbats "a23" or "BALLOT X" is encoded as 0x37 or "7"
                regex = '7\\s+This is radiobutton choice {}'.format(i)
            else:
                # Zapf Dingbats "a73" or "BALLOT SQUARE" is encoded as 0x6E or "n"
                regex = 'n\\s+This is radiobutton choice {}'.format(i)
            six.assertRegex(self, rendered_text, regex)
        self.assertIn('Extra text for choice 0', rendered_text)
        self.assertIn('Extra radiobutton answer text', rendered_text)

    def test_singleline_text_rendered(self):
        singleline_question = '''[
        { "answer": "Single line text answer",
        "id": 1,
        "section": 1,
        "question_text": "Single line text question?",
        "type": "SingleLineText"
        }
        ]'''
        report = PDFFullReport(self.report, singleline_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Single line text question?', rendered_text)
        self.assertIn('Single line text answer', rendered_text)

    def test_singleline_text_no_answer_rendered(self):
        singleline_question = '''[
        { "answer": "",
        "id": 1,
        "section": 1,
        "question_text": "Single line text question?",
        "type": "SingleLineText"
        }
        ]'''
        report = PDFFullReport(self.report, singleline_question)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        rendered_report = BytesIO(output)
        pdf_reader = PyPDF2.PdfFileReader(rendered_report)
        rendered_text = pdf_reader.getPage(1).extractText()

        self.assertIn('Single line text question?', rendered_text)
        self.assertIn('Not answered', rendered_text)


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
        self.assertIn("Reported by: dummy", pdfReader.getPage(0).extractText())
        self.assertIn("test answer", pdfReader.getPage(1).extractText())
        self.assertIn("answer to 2nd question", pdfReader.getPage(1).extractText())

    def test_pdf_report_generated_with_timestamp(self):
        # test_tzname matches TIME_ZONE in tests/settings.py
        test_tzname = 'Europe/Paris'
        report = PDFFullReport(self.report, self.decrypted_report)
        output = report.generate_pdf_report(recipient=None, report_id=None)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)
        date_format = "%m/%d/%Y @%H:%M%p"
        timezone.activate(pytz.timezone(test_tzname))
        expected_time = localtime(timezone.now()).strftime(date_format)
        self.assertIn(expected_time, pdfReader.getPage(0).extractText())

    def test_submission_to_school(self):
        EmailNotification.objects.create(name='report_delivery', subject="test delivery", body="test body")
        sent_full_report = SentFullReport.objects.create(report=self.report, to_address=settings.COORDINATOR_EMAIL)
        DeliveryApi().send_report_to_authority(sent_full_report, self.decrypted_report)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.attachments[0][0], 'report_%s.pdf.gpg' % sent_full_report.get_report_id())

    # TODO: test encryption of submitted report email

    def test_pdf_match_report_is_generated(self):
        match1_report_content = MatchReportContent(identifier='perp',
                                                   perp_name='Perperick',
                                                   email='email1@example.com',
                                                   phone='555-555-1212',
                                                   contact_name='Una',
                                                   voicemail='Yes')
        match1 = self.create_match(self.user1, 'perp', match1_report_content)
        match2_report_content = MatchReportContent(identifier='perp',
                                                   perp_name='Perpy',
                                                   email='email2@example.com',
                                                   phone='(000) 0000000',
                                                   contact_name='Ni',
                                                   notes='Please only call after 5pm')
        match2 = self.create_match(self.user2, 'perp', match2_report_content)
        report = PDFMatchReport([match1, match2], "perp")
        output = report.generate_match_report(report_id=1)
        exported_report = BytesIO(output)
        pdfReader = PyPDF2.PdfFileReader(exported_report)

        pdf_text = pdfReader.getPage(0).extractText()
        self.assertIn("Intended for: Title IX Coordinator Tatiana Nine", pdf_text)
        self.assertIn("Matching identifier: perp", pdf_text)
        self.assertIn("Name(s): Perpy, Perperick", pdf_text)
        # Report 1
        self.assertIn("Perpetrator name given: Perpy", pdf_text)
        self.assertIn("Reported by: ymmud", pdf_text)
        self.assertRegexpMatches(pdf_text,
                                 'Submitted to matching on: \d\d/\d\d/201\d @\d\d:\d\d[P|A]M')
        self.assertRegexpMatches(pdf_text,
                                 'Record created: \d\d/\d\d/201\d @\d\d:\d\d[P|A]M')
        self.assertIn("Full record submitted? No", pdf_text)
        self.assertIn("Name: Una", pdf_text)
        self.assertIn("Phone: 555-555-1212", pdf_text)
        self.assertIn("Voicemail preferences: Yes", pdf_text)
        self.assertIn("Email: email1@example.com", pdf_text)
        self.assertIn("Notes on preferred contact time of day, gender of admin, etc.:\nNone provided", pdf_text)
        # Report 2
        self.assertIn("Perpetrator name given: Perperick", pdf_text)
        self.assertIn("Reported by: dummy", pdf_text)
        self.assertIn("Name: Ni", pdf_text)
        self.assertIn("Phone: (000) 0000000", pdf_text)
        self.assertIn("Voicemail preferences: None provided", pdf_text)
        self.assertIn("Email: email2@example.com", pdf_text)
        self.assertIn(
            "Notes on preferred contact time of day, gender of admin, etc.:\nPlease only call after 5pm",
            pdf_text)

    def test_matches_to_school(self):
        EmailNotification.objects.create(name='match_delivery', subject="test match delivery", body="test match body")
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        DeliveryApi().send_matching_report_to_authority([match1, match2], "dummy")
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
        self.assertIn("Reported by: test@example.com", pdfReader.getPage(0).extractText())
