from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings
import gnupg
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak, ListFlowable, ListItem, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, ListStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from time import strftime
from django.utils.timezone import localtime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.doctemplate import Indenter
import json

from reports.models import PageBase
from .models import EmailNotification, SentFullReport, SentMatchReport

date_format = "%m/%d/%Y @%H:%M%p"

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
        self.setFont('OpenSans',12)
        self.drawRightString(width - margin, margin, "Page %d of %d" % (self._pageNumber, page_count))

def set_up_styles():
    def get_font_location(filename):
        return settings.APPS_DIR.path('fonts')(filename)

    pdfmetrics.registerFont(TTFont('Montserrat', get_font_location('Montserrat-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSans', get_font_location('OpenSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSans-Bold', get_font_location('OpenSans-ExtraBold.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSans-Italic', get_font_location('OpenSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans', get_font_location('DejaVuSans.ttf')))
    pdfmetrics.registerFontFamily('OpenSans', normal='OpenSans', bold='OpenSans-Bold', italic='OpenSans-Italic')

    styles=getSampleStyleSheet()
    headline_style = styles["Heading1"]
    headline_style.alignment = TA_CENTER
    headline_style.fontSize = 48
    headline_style.fontName = 'Montserrat'

    subtitle_style = styles["Heading2"]
    subtitle_style.fontSize = 24
    subtitle_style.fontName = 'OpenSans'
    subtitle_style.leading = 26
    subtitle_style.alignment = TA_CENTER

    report_title_style = styles["Heading3"]
    report_title_style.fontSize = 28
    report_title_style.fontName = 'Montserrat'
    report_title_style.leading = 36
    report_title_style.spaceBefore = 0
    report_title_style.alignment = TA_CENTER

    section_title_style = styles["Heading4"]
    section_title_style.fontSize = 18
    section_title_style.fontName = 'Montserrat'
    section_title_style.leading = 22
    section_title_style.spaceBefore = 20

    body_style = styles["Normal"]
    body_style.fontSize = 14
    body_style.fontName = 'OpenSans'
    body_style.leading = 17
    body_style.leftIndent = 25

    styles.add(ParagraphStyle(name='Notes',
                                  parent=styles['Normal'],
                                  fontSize=10,
                                  leading=14,
                                  leftIndent=45,
                                  alias='notes'))
    styles.add(ListStyle(
        name='answers_list',
        bulletFontName='DejaVuSans',
    ))

    styles.add(ParagraphStyle(name='Answers',
                                  parent=styles['Normal'],
                                  leftIndent=0,
                                  alias='answers'))
    return styles

def add_cover_page(Story, styles, title, toname):
    subtitle_style = styles["Heading2"]
    headline_style = styles["Heading1"]
    logo = settings.APPS_DIR.path('static/images')("callisto_logo.png")

    im = Image(logo, 3*inch, 3*inch)
    Story.append(im)
    Story.append(Spacer(1, 18))

    Story.append(Paragraph("CONFIDENTIAL", headline_style))

    Story.append(Spacer(1, 30))

    Story.append(Spacer(1, 40))
    Story.append(Paragraph(title, subtitle_style))
    Story.append(Spacer(1, 40))
    if toname:
        Story.append(Paragraph("Intended for: {0}, Title IX Coordinator".format(toname), subtitle_style))

    Story.append(PageBreak())

def get_header_footer(toname=settings.COORDINATOR_NAME):
    def func(canvas, doc):
        width, height = letter
        margin = 0.66 * 72
        canvas.saveState()
        canvas.setFillColor('gray')
        canvas.setFont('OpenSans',12)
        canvas.drawString(margin, height - margin, "CONFIDENTIAL")
        canvas.drawRightString(width - margin, height - margin, strftime("%d %b %Y %H:%M"))
        if toname:
            canvas.drawString(margin, margin, "Intended for: Title IX Coordinator %s" % toname)
        canvas.restoreState()
    return func

def generate_pdf_report(toname, user, report, decrypted_report, report_id):

    styles = set_up_styles()
    notes_style = styles["Notes"]
    answers_style = styles['Answers']
    body_style = styles["Normal"]
    section_title_style = styles["Heading4"]
    report_title_style = styles["Heading3"]

    #HELPERS

    def format_question(question, strikethrough=False):
        markup_open, markup_close = ('<strike>', '</strike>') if strikethrough else ('', '')
        return [Paragraph(markup_open + question + markup_close, body_style),
                Spacer(1, 16 if strikethrough else 4)]

    def add_question(question, strikethrough=False):
        for element in format_question(question, strikethrough):
            Story.append(element)

    def format_answer(text, answer_type):
        return ListItem(Paragraph(text,answers_style), value = answer_type, leftIndent=60)

    def format_answer_list(answers, keep_together = True):
        answers = ListFlowable(
                    answers,
                    bulletType='bullet',
                    style = styles["answers_list"])
        if keep_together:
            answers = KeepTogether(answers)
        return [answers, Spacer(1, 16)]

    def add_answer_list(answers, keep_together = True):
        for element in format_answer_list(answers, keep_together):
            Story.append(element)

    #TODO: make selected_answer kwargs
    #TODO: figure out how to keep question with answer
    def add_multiple_choice(question, answers, selected_answers, last_is_free_text=False):
        add_question(question)

        def build_list_item(index, text):
            markup_open, markup_close = ('<b>', '</b>') if (index in selected_answers) else ('', '')
            return format_answer((markup_open + text + markup_close),
                                free_text if last_is_free_text and (index == len(answers) - 1)
                                          else selected if (index in selected_answers)
                                          else unselected)

        add_answer_list([build_list_item(i, t) for i,t in enumerate(answers)])

    def render_question(question):
        type = question.get('type')
        if type == 'RadioButton' or type=='Checkbox':
            choices = []
            answer_ids = question.get('answer')
            answers = []
            for idx, choice in enumerate(question.get('choices')):
                choices.append(choice.get('choice_text'))
                if str(choice.get('id')) in answer_ids:
                    answers.append(idx)
            extra = question.get('extra')
            if extra:
                choices.append("<i>{0}</i>: {1}".format(extra.get('extra_text'), extra.get('answer')))
            add_multiple_choice(question.get('question_text'), choices, answers, last_is_free_text=bool(extra))
        elif type=='SingleLineText' or type=='Date' or type=='MultiLineText':
            add_question(question.get('question_text'))
            answer = question.get('answer').replace('\n','<br />\n') or '<i>Not answered</i>'
            add_answer_list([format_answer(answer, free_text)], keep_together=False)
        elif type=='FormSet':
            forms = question.get('answers')
            prompt = question.get('prompt').capitalize()
            if forms:
                for idx, form in enumerate(forms):
                    title = prompt
                    if len(forms) > 1:
                        title = title + " " + str(idx + 1)
                    add_question(title)
                    Story.append(Indenter(left=12))
                    for q in form:
                        render_question(q)
                    Story.append(Indenter(left=-12))
            else:
                add_question(prompt)
                Story.append(Indenter(left=12))
                add_question('<i>None added</i>')
                Story.append(Indenter(left=-12))

    # PREPARE PDF
    report_content = json.loads(decrypted_report)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,pagesize=letter,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=72)

    # COVER PAGE
    Story=[]
    if toname:
        report_title = "{0}<br />Callisto Report No.: {1}".format(settings.SCHOOL_LONGNAME, report_id)
    else:
        report_title = "{0}<br />Callisto Report".format(settings.SCHOOL_LONGNAME)
    add_cover_page(Story, styles, report_title, toname)

    # METADATA PAGE
    # TODO: change (with header & footer) for export
    Story.append(Paragraph("Callisto Report", report_title_style))

    Story.append(Paragraph("Overview", section_title_style))

    overview_body = "Submitted by: {0}<br/>".format(user.account.school_email)
    if toname:
        overview_body = overview_body + "Submitted on:  {0}<br/>".format(localtime(report.submitted_to_school).strftime(date_format))
    overview_body = overview_body + """Record Created: {0}
                                       Last Edited: {1}""".format(localtime(report.added).strftime(date_format),
                                                                  localtime(report.last_edited).strftime(date_format)
                                                                  if report.last_edited else "<i>Not edited</i>")
    overview_body = overview_body.replace('\n','<br />\n')

    Story.append(Paragraph(overview_body, body_style))

    if toname:
        Story.append(Paragraph("Contact Preferences", section_title_style))

        contact_body = """Name: {0}
                          Phone: {1}
                          Voicemail preferences: {2}
                          Email: {3}
                          Notes on preferred contact time of day, gender of admin, etc.:""".format(report.contact_name or "<i>None provided</i>",
                                                                                                   report.contact_phone,
                                                                                                   report.contact_voicemail or "None provided",
                                                                                                   report.contact_email).replace('\n','<br />\n')

        Story.append(Paragraph(contact_body, body_style))
        Story.append(Paragraph(report.contact_notes or "None provided", notes_style))

        Story.append(Paragraph("Opted Into Matching?", section_title_style))

        in_matching = "<b>Yes</b>/No"
        not_in_matching = "Yes/<b>No</b>"
        Story.append(Paragraph(in_matching if report.entered_into_matching else not_in_matching, body_style))
        matching_notes = """This student has elected NOT to provide the perpetrator identifier (Facebook URL) that would cause their report to trigger a match. In discussions, you may wish to ask whether they would be willing to enter into the matching system. """
        if not report.entered_into_matching:
            Story.append(Paragraph(matching_notes, notes_style))

    Story.append(Paragraph("Key", section_title_style))

    unselected = u'\u2610'
    selected =  u'\u2717'
    free_text = u'\u2756'
    no_bullet = ' '

    key = ListFlowable(
        [ListItem(Paragraph("Unselected option",answers_style), value = unselected, leftIndent=45),
         ListItem(Paragraph("<b>Selected option</b>",answers_style), value = selected, leftIndent=45),
         ListItem(Paragraph("Free text response",answers_style), value = free_text, leftIndent=45),
         ListItem(Paragraph("<strike>question not shown (not relevant)</strike>",answers_style), value = no_bullet, leftIndent=45)],
        bulletType='bullet',
        style = styles["answers_list"] )
    Story.append(key)

    Story.append(PageBreak())

    # REPORT

    for section_id, section_name in PageBase.SECTION_CHOICES:
        Story.append(Paragraph(section_name, section_title_style))
        section_qs = [x for x in report_content if x.get('section') == section_id]
        for q in section_qs:
            render_question(q)

    doc.build(Story, onFirstPage=get_header_footer(toname), onLaterPages=get_header_footer(toname), canvasmaker=NumberedCanvas)
    result = buffer.getvalue()
    buffer.close()
    return result


def send_email_to_coordinator(pdf_to_attach, notification_name, report_id):
    notification = EmailNotification.objects.get(name=notification_name)

    from_email = '"Callisto Reports" <reports@{0}>'.format(settings.APP_URL)
    to = settings.COORDINATOR_EMAIL

    email = EmailMultiAlternatives(notification.subject, notification.render_body_plain(), from_email, [to])
    email.attach_alternative(notification.render_body(), "text/html")

    gpg = gnupg.GPG()
    school_public_key = settings.COORDINATOR_PUBLIC_KEY
    imported_keys = gpg.import_keys(school_public_key)
    #TODO: sign encrypted doc
    attachment = gpg.encrypt(pdf_to_attach, imported_keys.fingerprints[0], armor=True, always_trust=True)

    #TODO: include ID in filename
    email.attach("callisto_report_{0}.pdf.gpg".format(report_id), attachment.data, "application/octet-stream")

    email.send()

def send_report_to_school(user, report, decrypted_report):
    report_id = SentFullReport.objects.create(report=report, to_address=settings.COORDINATOR_EMAIL).get_report_id()
    pdf = generate_pdf_report(settings.COORDINATOR_NAME, user, report, decrypted_report, report_id)
    send_email_to_coordinator(pdf, 'report_delivery', report_id)

def generate_match_report(matches, report_id):
    styles = set_up_styles()
    notes_style = styles["Notes"]
    body_style = styles["Normal"]
    section_title_style = styles["Heading4"]
    report_title_style = styles["Heading3"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,pagesize=letter,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=72)
    # COVER PAGE
    Story=[]
    report_title = "{0}<br />Callisto Match Report No.: {1}".format(settings.SCHOOL_LONGNAME, report_id)
    add_cover_page(Story, styles, report_title, settings.COORDINATOR_NAME)


    # MATCH REPORTS
    Story.append(Paragraph("Callisto Match Report", report_title_style))

    Story.append(Paragraph("Perpetrator", section_title_style))
    names = ', '.join(set([match.name.strip() for match in matches if match.name]))
    if len(names) < 1:
        names = '<i>None provided</i>'
    perp_info = ('Name(s): ' + names) + '<br/>'+ matches[0].identifier
    Story.append(Paragraph(perp_info, body_style))


    for idx, match in enumerate(sorted(matches, key=lambda match: match.added, reverse=True)):
        Story.append(Paragraph("Report " + str(idx + 1), section_title_style))

        report = match.report
        user = report.owner
        if report.submitted_to_school:
            sent_report = report.sentfullreport_set.first()
            report_id = sent_report.get_report_id() if sent_report else "<i>Not found</i>"
            is_submitted = """Yes
                           Submitted to school on: {0}
                           Submitted report ID: {1}""".format(localtime(report.submitted_to_school).strftime(date_format),
                                                                report_id)
        else:
            is_submitted = "No"
        overview_body = """Perpetrator name given: {0}
                           Submitted by: {1}
                           Submitted to matching on: {2}
                           Record Created: {3}
                           Full record submitted? {4}""".format(match.name or "<i>None provided</i>",
                                                                user.account.school_email,
                                                                localtime(match.added).strftime(date_format),
                                                                localtime(report.added).strftime(date_format),
                                                                is_submitted).replace('\n','<br />\n')

        Story.append(Paragraph(overview_body, body_style))

        contact_body = """<br/>Name: {0}
                          Phone: {1}
                          Voicemail preferences: {2}
                          Email: {3}
                          Notes on preferred contact time of day, gender of admin, etc.:""".format(match.contact_name or "<i>None provided</i>",
                                                                                                   match.contact_phone,
                                                                                                   match.contact_voicemail or "<i>None provided</i>",
                                                                                                   match.contact_email).replace('\n','<br />\n')

        Story.append(Paragraph(contact_body, body_style))
        Story.append(Paragraph(match.contact_notes or "None provided", notes_style))

    doc.build(Story, onFirstPage=get_header_footer, onLaterPages=get_header_footer, canvasmaker=NumberedCanvas)
    result = buffer.getvalue()
    buffer.close()
    return result

def send_matching_report_to_school(matches):
    #TODO: set matches
    sent_report = SentMatchReport.objects.create(to_address = settings.COORDINATOR_EMAIL)
    report_id = sent_report.get_report_id()
    sent_report.reports.add(*matches)
    sent_report.save()
    pdf = generate_match_report(matches, report_id)
    send_email_to_coordinator(pdf, 'match_delivery', report_id)