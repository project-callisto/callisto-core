import os
import json
import logging
from collections import OrderedDict
from io import BytesIO

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ListStyle, ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, PageBreak

from django.conf import settings
from django.utils import timezone
from django.utils.html import conditional_escape

from callisto_core.utils import api

logger = logging.getLogger(__name__)


def report_as_pdf(report, data, recipient):
    return PDFFullReport(
        report=report,
        report_data=data,
    ).generate_pdf_report(
        recipient=recipient,
        report_id=report.id,
    )


class MatchReportContent(object):
    '''
        Class to structure contact information collected
        from match submission form for report
    '''

    # This constructor is called with keyword arguments populated by
    # encrypted data. Existing arguments should not be removed or renamed,
    # and new arguments must have default values.
    def __init__(
        self, identifier, perp_name, email, phone,
        contact_name=None, voicemail=None, notes=None,
    ):
        self.identifier = conditional_escape(identifier)
        self.perp_name = conditional_escape(perp_name)
        self.contact_name = conditional_escape(contact_name)
        self.email = conditional_escape(email)
        self.phone = conditional_escape(phone)
        self.voicemail = conditional_escape(voicemail)
        self.notes = conditional_escape(notes)

    @classmethod
    def from_form(cls, form):
        return cls(
            identifier=form.cleaned_data.get('identifier'),
            perp_name=form.cleaned_data.get('perp_name'),
            contact_name=form.instance.report.contact_name,
            email=form.instance.report.contact_email,
            phone=form.instance.report.contact_phone,
            voicemail=form.instance.report.contact_voicemail,
            notes=form.instance.report.contact_notes,
        )


class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        '''add page info to each page (page x of y)'''
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
        self.drawRightString(
            width - margin, margin, "Page %d of %d" %
            (self._pageNumber, page_count))


class PDFReport(object):

    unselected = u'\u2610'
    selected = u'\u2717'
    free_text = u'\u2756'
    no_bullet = ' '

    report_title = "Report"

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
        '''
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
        '''
        def get_font_location(filename):
            return settings.APPS_DIR.path('fonts')(filename)

        styles = getSampleStyleSheet()
        headline_style = styles["Heading1"]
        headline_style.alignment = TA_CENTER
        headline_style.fontSize = 48

        subtitle_style = styles["Heading2"]
        subtitle_style.fontSize = 24
        subtitle_style.leading = 26
        subtitle_style.alignment = TA_CENTER

        report_title_style = styles["Heading3"]
        report_title_style.fontSize = 28
        report_title_style.leading = 36
        report_title_style.spaceBefore = 0
        report_title_style.alignment = TA_CENTER

        section_title_style = styles["Heading4"]
        section_title_style.fontSize = 18
        section_title_style.leading = 22
        section_title_style.spaceBefore = 20

        body_style = styles["Normal"]
        body_style.fontSize = 14
        body_style.leading = 17
        body_style.leftIndent = 25

        styles.add(ParagraphStyle(
            name='Notes',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            leftIndent=45,
            alias='notes',
        ))
        styles.add(ListStyle(
            name='AnswersList',
        ))
        styles.add(ParagraphStyle(
            name='Answers',
            parent=styles['Normal'],
            leftIndent=0,
            alias='answers',
        ))

        return styles

    # FORMATTING HELPERS

    def add_question(self, question):
        self.pdf_elements.append(
            Paragraph(question, self.body_style),
        )
        self.pdf_elements.append(Spacer(1, 4))

    def add_answer_list(self, answers):
        for answer in answers:
            self.pdf_elements.append(
                Paragraph(answer, self.notes_style),
            )
            self.pdf_elements.append(Spacer(1, 1))

    def render_question(self, question, answers):
        self.add_question(question)
        self.add_answer_list(answers)

    def get_header_footer(self, recipient):
        def func(canvas, doc):
            width, height = letter
            margin = 0.66 * 72
            canvas.saveState()
            canvas.setFillColor('gray')
            canvas.drawString(margin, height - margin, "CONFIDENTIAL")
            canvas.drawRightString(
                width - margin, height - margin, str(timezone.now()))
            canvas.drawString(
                margin, margin,
                f"Intended for: Title IX Coordinator {recipient}",
            )
            canvas.restoreState()
        return func

    @staticmethod
    def get_user_identifier(user):
        try:
            return user.email or user.username
        except AttributeError:
            return 'Anonymous User'


class PDFUserReviewReport(PDFReport):

    title = 'User Review Report'

    def cover_page(self):
        styles = getSampleStyleSheet()
        headline_style = styles["Heading1"]
        headline_style.alignment = TA_CENTER
        headline_style.fontSize = 48
        subtitle_style = styles["Heading2"]
        subtitle_style.fontSize = 24
        subtitle_style.leading = 26
        subtitle_style.alignment = TA_CENTER
        return [
            Image(
                os.path.join(settings.BASE_DIR, api.NotificationApi.logo_path),
                3 * inch,
                3 * inch,
            ),
            Spacer(1, 18),
            Paragraph("CONFIDENTIAL", headline_style),
            Spacer(1, 30),
            Spacer(1, 40),
            Paragraph(self.title, subtitle_style),
            Spacer(1, 40),
            # Paragraph(
            #     f"Intended for: {recipient}, Title IX Coordinator",
            #     subtitle_style,
            # ),
            PageBreak(),
        ]

    @classmethod
    def generate(cls, pdf_input_data):
        self = cls()

        # pre-setup
        report_buffer = BytesIO()
        doc = SimpleDocTemplate(
            report_buffer,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72,
        )

        # fill with content
        self.pdf_elements.extend(self.cover_page())

        # post-setup
        doc.build(
            self.pdf_elements,
            canvasmaker=NumberedCanvas,
        )
        result = report_buffer.getvalue()
        report_buffer.close()
        return result


class PDFFullReport(PDFReport):

    def __init__(self, report, report_data):
        super().__init__()
        self.report = report
        self.report_data = report_data

    def get_metadata_page(self, recipient):
        MetadataPage = []
        MetadataPage.append(Paragraph(
            api.NotificationApi.report_title,
            self.report_title_style,
        ))

        MetadataPage.append(Paragraph("Overview", self.section_title_style))

        overview_body = "Reported by: {0}<br/>".format(
            self.get_user_identifier(self.report.owner),
        )
        overview_body = overview_body + '''
            Submitted on: {0}<br/>
        '''.format(
            self.report.submitted_to_school,
        )
        overview_body = overview_body + '''
            Record Created: {0}<br />
        '''.format(self.report.added.strftime("%Y-%m-%d %H:%M"))

        MetadataPage.append(Paragraph(overview_body, self.body_style))

        MetadataPage.append(Paragraph(
            "Contact Preferences",
            self.section_title_style,
        ))

        contact_body = '''
            Name: {0}<br />
            Phone: {1}<br />
            Voicemail preferences: {2}<br />
            Email: {3}<br />
            Notes on preferred contact time of day, gender of admin, etc.:
        '''.format(
            self.report.contact_name or "<i>None provided</i>",
            self.report.contact_phone,
            self.report.contact_voicemail or "None provided",
            self.report.contact_email,
        )

        MetadataPage.append(Paragraph(
            contact_body,
            self.body_style,
        ))
        MetadataPage.append(Paragraph(
            self.report.contact_notes or "None provided",
            self.notes_style,
        ))

        return MetadataPage

    def generate_pdf_report(self, report_id, recipient):
        # PREPARE PDF
        report_buffer = BytesIO()
        doc = SimpleDocTemplate(
            report_buffer,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72,
        )

        # COVER PAGE
        self.pdf_elements.extend(
            api.NotificationApi.get_cover_page(
                report_id=report_id,
                recipient=recipient,
            ),
        )

        # METADATA PAGE
        self.pdf_elements.extend(self.get_metadata_page(recipient))

        # REPORT
        self.pdf_elements.extend(
            [Paragraph("Report Questions", self.section_title_style)],
        )
        for item in self.report_data:
            question, answers = item.popitem()
            self.render_question(question, answers)

        doc.build(
            self.pdf_elements,
            onFirstPage=self.get_header_footer(recipient),
            onLaterPages=self.get_header_footer(recipient),
            canvasmaker=NumberedCanvas,
        )
        result = report_buffer.getvalue()
        report_buffer.close()
        return result


class PDFMatchReport(PDFReport):

    report_title = "Match Report"

    def __init__(self, matches, identifier):
        super(PDFMatchReport, self).__init__()
        self.matches = sorted(
            matches,
            key=lambda m: m.added.strftime("%Y-%m-%d %H:%M"),
            reverse=True)
        self.identifier = identifier

    def generate_match_report(self, report_id, recipient):
        '''
        Generates PDF report about a discovered match.

        Args:
          report_id (str): id used to uniquely identify this report to receiving authority

        Returns:
          bytes: a PDF with the submitted perp information & contact information of the reporters for this match

        '''
        matches_with_reports = [
            (match,
             MatchReportContent(
                 **json.loads(match.get_match(self.identifier))))
            for match in self.matches]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72,
        )
        # COVER PAGE
        self.pdf_elements.extend(
            api.NotificationApi.get_cover_page(
                report_id=report_id,
                recipient=recipient,
            ),
        )

        # MATCH REPORTS
        self.pdf_elements.append(
            Paragraph(
                api.NotificationApi.report_title,
                self.report_title_style,
            )
        )

        # perpetrator info
        self.pdf_elements.append(
            Paragraph(
                "Perpetrator",
                self.section_title_style,
            )
        )
        names = ', '.join(OrderedDict.fromkeys([report.perp_name.strip(
        ) for _, report in matches_with_reports if report.perp_name]))
        if len(names) < 1:
            names = '<i>None provided</i>'
        perp_info = ('Name(s): ' + names) + '<br/>' + \
            "Matching identifier: " + self.identifier
        self.pdf_elements.append(Paragraph(perp_info, self.body_style))

        # reporter info
        for idx, (match_report, match_report_content) in enumerate(
                matches_with_reports):
            self.pdf_elements.append(
                Paragraph(
                    "Report " + str(idx + 1),
                    self.section_title_style,
                )
            )

            report = match_report.report
            user = report.owner

            if report.submitted_to_school:
                sent_report = report.sentfullreport_set.first()
                report_id = sent_report.get_report_id() if sent_report else "<i>Not found</i>"
                is_submitted = '''
                    Yes
                    Submitted to school on: {0}
                    Submitted report ID: {1}
                '''.format(
                    report.submitted_to_school,
                    report_id,
                )
            else:
                is_submitted = "No"

            overview_body = '''
                Perpetrator name given: {0}
                Reported by: {1}
                Submitted to matching on: {2}
                Record created: {3}
                Full record submitted? {4}
            '''.format(
                match_report_content.perp_name or "<i>None provided</i>",
                self.get_user_identifier(user),
                match_report.added.strftime("%Y-%m-%d %H:%M"),
                report.added.strftime("%Y-%m-%d %H:%M"),
                is_submitted,
            ).replace('\n', '<br />\n')

            self.pdf_elements.append(Paragraph(overview_body, self.body_style))

            contact_body = '''<br/>Name: {0}
                              Phone: {1}
                              Voicemail preferences: {2}
                              Email: {3}
                              Notes on preferred contact time of day, gender of admin, etc.:'''.format(
                match_report_content.contact_name or "<i>None provided</i>",
                match_report_content.phone,
                match_report_content.voicemail or "<i>None provided</i>",
                match_report_content.email).replace('\n', '<br />\n')

            self.pdf_elements.append(Paragraph(contact_body, self.body_style))
            self.pdf_elements.append(Paragraph(
                match_report_content.notes or "None provided",
                self.notes_style,
            ))

        doc.build(
            self.pdf_elements,
            onFirstPage=self.get_header_footer(recipient),
            onLaterPages=self.get_header_footer(recipient),
            canvasmaker=NumberedCanvas,
        )
        result = buffer.getvalue()
        buffer.close()
        return result
