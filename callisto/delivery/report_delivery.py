import json
import logging
from collections import OrderedDict
from io import BytesIO

import gnupg
import pytz
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ListStyle, ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer,
)
from reportlab.platypus.doctemplate import Indenter
from wizard_builder.models import PageBase

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.timezone import localtime

from .models import EmailNotification, SentFullReport, SentMatchReport

date_format = "%m/%d/%Y @%H:%M%p"
# TODO: customize https://github.com/SexualHealthInnovations/callisto-core/issues/20
tzname = 'America/Los_Angeles'
timezone.activate(pytz.timezone(tzname))
logger = logging.getLogger(__name__)


class MatchReportContent:
    """ Class to structure contact information collected from match submission form for report """

    def __init__(self, identifier, perp_name, email, phone, contact_name=None, voicemail=None, notes=None):
        self.identifier = identifier
        self.perp_name = perp_name
        self.contact_name = contact_name
        self.email = email
        self.phone = phone
        self.voicemail = voicemail
        self.notes = notes


class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        width, height = letter
        margin = 0.66 * 72
        self.setFillColor('gray')
        # self.setFont('OpenSans',12)
        self.drawRightString(width - margin, margin, "Page %d of %d" % (self._pageNumber, page_count))


class PDFReport(object):

    unselected = u'\u2610'
    selected = u'\u2717'
    free_text = u'\u2756'
    no_bullet = ' '

    report_title = "Report"
    from_email = '"Reports" <reports@{0}>'.format(settings.APP_URL)
    report_filename = "report_{0}.pdf.gpg"

    def __init__(self):
        self.styles = self.set_up_styles()
        self.notes_style = self.styles['Notes']
        self.answers_style = self.styles['Answers']
        self.answers_list_style = self.styles['AnswersList']
        self.body_style = self.styles['Normal']
        self.section_title_style = self.styles['Heading4']
        self.report_title_style = self.styles['Heading3']
        self.pdf_elements = []

    def set_up_styles(self, *args, **kwargs):
        """
        Helper formatting methods assume the following styles have been defined:
            * Normal: format_question, get_metadata_page
            * Notes: get_metadata_page
            * Answers: format_answer, get_metadata_page
            * AnswersList: format_answer_list, get_metadata_page
            * Heading4: get_metadata_page, PDFFullReport.generate_pdf_report, PDFMatchReport.generate_match_report
            * Heading3: get_metadata_page, PDFMatchReport.generate_match_report
        If you override this method but don't define these styles, you will need to also override init and potentially
        the corresponding formatting methods.
        :return: a ReportLab stylesheet
        """
        def get_font_location(filename):
            return settings.APPS_DIR.path('fonts')(filename)

        # pdfmetrics.registerFont(TTFont('Montserrat', get_font_location('Montserrat-Regular.ttf')))
        # pdfmetrics.registerFont(TTFont('OpenSans', get_font_location('OpenSans-Regular.ttf')))
        # pdfmetrics.registerFont(TTFont('OpenSans-Bold', get_font_location('OpenSans-ExtraBold.ttf')))
        # pdfmetrics.registerFont(TTFont('OpenSans-Italic', get_font_location('OpenSans-Italic.ttf')))
        # pdfmetrics.registerFont(TTFont('DejaVuSans', get_font_location('DejaVuSans.ttf')))
        # pdfmetrics.registerFontFamily('OpenSans', normal='OpenSans', bold='OpenSans-Bold', italic='OpenSans-Italic')

        styles = getSampleStyleSheet()
        headline_style = styles["Heading1"]
        headline_style.alignment = TA_CENTER
        headline_style.fontSize = 48
        # headline_style.fontName = 'Montserrat'

        subtitle_style = styles["Heading2"]
        subtitle_style.fontSize = 24
        # subtitle_style.fontName = 'OpenSans'
        subtitle_style.leading = 26
        subtitle_style.alignment = TA_CENTER

        report_title_style = styles["Heading3"]
        report_title_style.fontSize = 28
        # report_title_style.fontName = 'Montserrat'
        report_title_style.leading = 36
        report_title_style.spaceBefore = 0
        report_title_style.alignment = TA_CENTER

        section_title_style = styles["Heading4"]
        section_title_style.fontSize = 18
        # section_title_style.fontName = 'Montserrat'
        section_title_style.leading = 22
        section_title_style.spaceBefore = 20

        body_style = styles["Normal"]
        body_style.fontSize = 14
        # body_style.fontName = 'OpenSans'
        body_style.leading = 17
        body_style.leftIndent = 25

        styles.add(ParagraphStyle(name='Notes',
                                  parent=styles['Normal'],
                                  fontSize=10,
                                  leading=14,
                                  leftIndent=45,
                                  alias='notes'))
        styles.add(ListStyle(
            name='AnswersList',
            # bulletFontName='DejaVuSans',
        ))

        styles.add(ParagraphStyle(name='Answers',
                                  parent=styles['Normal'],
                                  leftIndent=0,
                                  alias='answers'))

        return styles

    # FORMATTING HELPERS

    def format_question(self, question, strikethrough=False):
        markup_open, markup_close = ('<strike>', '</strike>') if strikethrough else ('', '')
        return [Paragraph(markup_open + question + markup_close, self.body_style),
                Spacer(1, 16 if strikethrough else 4)]

    def add_question(self, question, strikethrough=False):
        for element in self.format_question(question, strikethrough):
            self.pdf_elements.append(element)

    def format_answer(self, text, answer_type):
        """
        Expects text to be already escaped
        """
        return ListItem(Paragraph(text, self.answers_style), value=answer_type, leftIndent=60)

    def format_answer_list(self, answers, keep_together=True):
        answers = ListFlowable(
            answers,
            bulletType='bullet',
            style=self.answers_list_style)
        if keep_together:
            answers = KeepTogether(answers)
        return [answers, Spacer(1, 16)]

    def add_answer_list(self, answers, keep_together=True):
        for element in self.format_answer_list(answers, keep_together):
            self.pdf_elements.append(element)

    # TODO: figure out how to keep question w answer https://github.com/SexualHealthInnovations/callisto-core/issues/34
    def add_multiple_choice(self, question, answers, selected_answers, last_is_free_text=False):
        self.add_question(question)

        def build_list_item(index, text):
            markup_open, markup_close = ('<b>', '</b>') if (index in selected_answers) else ('', '')
            return self.format_answer((markup_open + conditional_escape(text) + markup_close),
                                      self.free_text if last_is_free_text and (index == len(answers) - 1)
                                      else self.selected if (index in selected_answers)
                                      else self.unselected)

        self.add_answer_list([build_list_item(i, t) for i, t in enumerate(answers)])

    def render_question(self, question):
        question_type = question.get('type')
        if question_type == 'RadioButton' or question_type == 'Checkbox':
            choices = []
            answer_ids = conditional_escape(question.get('answer'))
            # RadioButton answers need to be stored as single int to keep edit working
            if answer_ids and question_type == 'RadioButton':
                answer_ids = [answer_ids]
            answers = []
            for idx, choice in enumerate(question.get('choices')):
                choices.append(choice.get('choice_text'))
                if str(choice.get('id')) in answer_ids:
                    answers.append(idx)
            extra = question.get('extra')
            if extra:
                choices.append("<i>{0}</i>: {1}".format(extra.get('extra_text'), extra.get('answer')))
            self.add_multiple_choice(question.get('question_text'), choices, answers, last_is_free_text=bool(extra))
        elif question_type == 'SingleLineText' or question_type == 'Date' or question_type == 'MultiLineText':
            self.add_question(question.get('question_text'))
            answer = conditional_escape(question.get('answer')).replace('\n', '<br />\n') or '<i>Not answered</i>'
            self.add_answer_list([self.format_answer(answer, self.free_text)], keep_together=False)
        elif question_type == 'FormSet':
            forms = question.get('answers')
            prompt = question.get('prompt').capitalize()
            if forms:
                for idx, form in enumerate(forms):
                    title = prompt
                    if len(forms) > 1:
                        title = title + " " + str(idx + 1)
                    self.add_question(title)
                    self.pdf_elements.append(Indenter(left=12))
                    for q in form:
                        self.render_question(q)
                    self.pdf_elements.append(Indenter(left=-12))
            else:
                self.add_question(prompt)
                self.pdf_elements.append(Indenter(left=12))
                self.add_question('<i>None added</i>')
                self.pdf_elements.append(Indenter(left=-12))

    def get_cover_page(self, report_id, recipient, *args, **kwargs):
        CoverPage = []
        return CoverPage

    def get_header_footer(self, recipient=settings.COORDINATOR_NAME):
        def func(canvas, doc):
            width, height = letter
            margin = 0.66 * 72
            canvas.saveState()
            canvas.setFillColor('gray')
            # canvas.setFont('OpenSans',12)
            canvas.drawString(margin, height - margin, "CONFIDENTIAL")
            canvas.drawRightString(width - margin, height - margin, localtime(timezone.now()).strftime(date_format))
            if recipient:
                canvas.drawString(margin, margin, "Intended for: Title IX Coordinator %s" % recipient)
            canvas.restoreState()
        return func

    def send_email_to_coordinator(self, pdf_to_attach, notification_name, report_id):
        notification = EmailNotification.objects.get(name=notification_name)

        to = settings.COORDINATOR_EMAIL

        email = EmailMultiAlternatives(notification.subject, notification.render_body_plain(), self.from_email, [to])
        email.attach_alternative(notification.render_body(), "text/html")

        gpg = gnupg.GPG()
        school_public_key = settings.COORDINATOR_PUBLIC_KEY
        imported_keys = gpg.import_keys(school_public_key)
        # TODO: sign encrypted doc https://github.com/SexualHealthInnovations/callisto-core/issues/32
        attachment = gpg.encrypt(pdf_to_attach, imported_keys.fingerprints[0], armor=True, always_trust=True)

        email.attach(self.report_filename.format(report_id), attachment.data, "application/octet-stream")

        email.send()

    @staticmethod
    def get_user_identifier(user):
        return user.email or user.username


class PDFFullReport(PDFReport):

    def __init__(self, report, decrypted_report):
        super(PDFFullReport, self).__init__()
        self.user = report.owner
        self.report = report
        self.decrypted_report = decrypted_report

    def send_report_to_school(self):
        logger.info("sending report to reporting authority")
        report_id = SentFullReport.objects.create(
            report=self.report, to_address=settings.COORDINATOR_EMAIL).get_report_id()
        self.report.submitted_to_school = timezone.now()
        pdf = self.generate_pdf_report(report_id)
        self.send_email_to_coordinator(pdf, 'report_delivery', report_id)
        # save report timestamp only if generation & email work
        self.report.save()

    def get_metadata_page(self, recipient):
        MetadataPage = []
        MetadataPage.append(Paragraph(self.report_title, self.report_title_style))

        MetadataPage.append(Paragraph("Overview", self.section_title_style))

        overview_body = "Reported by: {0}<br/>".format(self.get_user_identifier(self.user))
        if recipient:
            overview_body = overview_body + "Submitted on:  {0}<br/>".format(localtime(self.report.submitted_to_school)
                                                                             .strftime(date_format))
        overview_body = overview_body + \
            """Record Created: {0}
            Last Edited: {1}""".format(localtime(self.report.added).strftime(date_format),
                                       localtime(self.report.last_edited).strftime(date_format)
                                       if self.report.last_edited else "<i>Not edited</i>")
        overview_body = overview_body.replace('\n', '<br />\n')

        MetadataPage.append(Paragraph(overview_body, self.body_style))

        if recipient:
            MetadataPage.append(Paragraph("Contact Preferences", self.section_title_style))

            contact_body = """Name: {0}
            Phone: {1}
            Voicemail preferences: {2}
            Email: {3}
            Notes on preferred contact time of day, gender of admin, etc.:""".format(
                self.report.contact_name or "<i>None provided</i>",
                self.report.contact_phone,
                self.report.contact_voicemail or "None provided",
                self.report.contact_email).replace('\n', '<br />\n')

            MetadataPage.append(Paragraph(contact_body, self.body_style))
            MetadataPage.append(Paragraph(self.report.contact_notes or "None provided", self.notes_style))

        MetadataPage.append(Paragraph("Key", self.section_title_style))

        key = ListFlowable(
            [ListItem(Paragraph("Unselected option", self.answers_style), value=self.unselected, leftIndent=45),
             ListItem(Paragraph("<b>Selected option</b>", self.answers_style), value=self.selected, leftIndent=45),
             ListItem(Paragraph("Free text response", self.answers_style), value=self.free_text, leftIndent=45)],
            bulletType='bullet',
            style=self.answers_list_style)
        MetadataPage.append(key)

        MetadataPage.append(PageBreak())
        return MetadataPage

    def generate_pdf_report(self, report_id, recipient=settings.COORDINATOR_NAME):

        # PREPARE PDF
        report_content = json.loads(self.decrypted_report)

        report_buffer = BytesIO()
        doc = SimpleDocTemplate(report_buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)

        # COVER PAGE
        self.pdf_elements.extend(self.get_cover_page(report_id=report_id, recipient=recipient))

        # METADATA PAGE
        self.pdf_elements.extend(self.get_metadata_page(recipient))

        # REPORT
        for section_id, section_name in PageBase.SECTION_CHOICES:
            self.pdf_elements.append(Paragraph(section_name, self.section_title_style))
            section_qs = [x for x in report_content if x.get('section') == section_id]
            for q in section_qs:
                self.render_question(q)

        doc.build(self.pdf_elements, onFirstPage=self.get_header_footer(recipient),
                  onLaterPages=self.get_header_footer(recipient), canvasmaker=NumberedCanvas)
        result = report_buffer.getvalue()
        report_buffer.close()
        return result


class PDFMatchReport(PDFReport):

    report_title = "Match Report"

    def __init__(self, matches, identifier):
        super(PDFMatchReport, self).__init__()
        self.matches = sorted(matches, key=lambda m: m.added, reverse=True)
        self.identifier = identifier

    def generate_match_report(self, report_id):
        """
        Generates PDF report about a discovered match.

        Args:
          report_id (str): id used to uniquely identify this report to receiving authority

        Returns:
          bytes: a PDF with the submitted perp information & contact information of the reporters for this match

        """

        matches_with_reports = [(match, MatchReportContent(**json.loads(match.get_match(self.identifier))))
                                for match in self.matches]

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        # COVER PAGE
        self.pdf_elements.extend(self.get_cover_page(report_id=report_id, recipient=settings.COORDINATOR_NAME))

        # MATCH REPORTS
        self.pdf_elements.append(Paragraph(self.report_title, self.report_title_style))

        # perpetrator info
        self.pdf_elements.append(Paragraph("Perpetrator", self.section_title_style))
        names = ', '.join(OrderedDict.fromkeys([report.perp_name.strip() for _, report in matches_with_reports
                                                if report.perp_name]))
        if len(names) < 1:
            names = '<i>None provided</i>'
        perp_info = ('Name(s): ' + names) + '<br/>' + "Matching identifier: " + self.identifier
        self.pdf_elements.append(Paragraph(perp_info, self.body_style))

        # reporter info
        for idx, (match_report, match_report_content) in enumerate(matches_with_reports):
            self.pdf_elements.append(Paragraph("Report " + str(idx + 1), self.section_title_style))

            report = match_report.report
            user = report.owner

            if report.submitted_to_school:
                sent_report = report.sentfullreport_set.first()
                report_id = sent_report.get_report_id() if sent_report else "<i>Not found</i>"
                is_submitted = """Yes
                               Submitted to school on: {0}
                               Submitted report ID: {1}""".format(
                    localtime(report.submitted_to_school).strftime(date_format),
                    report_id)
            else:
                is_submitted = "No"

            overview_body = """Perpetrator name given: {0}
                               Reported by: {1}
                               Submitted to matching on: {2}
                               Record created: {3}
                               Full record submitted? {4}""".format(
                match_report_content.perp_name or "<i>None provided</i>",
                self.get_user_identifier(user),
                localtime(match_report.added).strftime(date_format),
                localtime(report.added).strftime(date_format),
                is_submitted).replace('\n', '<br />\n')

            self.pdf_elements.append(Paragraph(overview_body, self.body_style))

            contact_body = """<br/>Name: {0}
                              Phone: {1}
                              Voicemail preferences: {2}
                              Email: {3}
                              Notes on preferred contact time of day, gender of admin, etc.:""".format(
                match_report_content.contact_name or "<i>None provided</i>",
                match_report_content.phone,
                match_report_content.voicemail or "<i>None provided</i>",
                match_report_content.email).replace('\n', '<br />\n')

            self.pdf_elements.append(Paragraph(contact_body, self.body_style))
            self.pdf_elements.append(Paragraph(match_report_content.notes or "None provided",
                                               self.notes_style))

        doc.build(self.pdf_elements, onFirstPage=self.get_header_footer(), onLaterPages=self.get_header_footer(),
                  canvasmaker=NumberedCanvas)
        result = buffer.getvalue()
        buffer.close()
        return result

    def send_matching_report_to_school(self):
        """ Encrypts the generated PDF with GPG and attaches it to an email to the reporting authority """
        logger.info("sending match report to reporting authority")
        sent_report = SentMatchReport.objects.create(to_address=settings.COORDINATOR_EMAIL)
        report_id = sent_report.get_report_id()
        sent_report.reports.add(*self.matches)
        sent_report.save()
        pdf = self.generate_match_report(report_id)
        self.send_email_to_coordinator(pdf, 'match_delivery', report_id)
