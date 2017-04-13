import logging

import gnupg
import pytz

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone

from callisto.delivery.models import SentMatchReport
from callisto.notification.models import EmailNotification

logger = logging.getLogger(__name__)
tzname = settings.REPORT_TIME_ZONE or 'America/Los_Angeles'
timezone.activate(pytz.timezone(tzname))


class NotificationApi(object):

    model = EmailNotification
    report_filename = "report_{0}.pdf.gpg"
    from_email = '"Reports" <reports@{0}>'.format(settings.APP_URL)

    @classmethod
    def send_report_to_school(cls, sent_full_report, decrypted_report):
        # TODO: https://github.com/SexualHealthInnovations/callisto-core/issues/150
        from callisto.delivery.report_delivery import PDFFullReport

        logger.info("sending report to reporting authority")
        pdf_report_id = sent_full_report.get_report_id()
        sent_full_report.report.submitted_to_school = timezone.now()
        pdf = PDFFullReport(sent_full_report.report, decrypted_report).generate_pdf_report(pdf_report_id)
        cls.send_email_to_coordinator(pdf, 'report_delivery', pdf_report_id)
        # save report timestamp only if generation & email work
        sent_full_report.report.save()

    @classmethod
    def send_matching_report_to_school(cls, matches, identifier):
        """ Encrypts the generated PDF with GPG and attaches it to an email to the reporting authority """
        # TODO: https://github.com/SexualHealthInnovations/callisto-core/issues/150
        from callisto.delivery.report_delivery import PDFMatchReport

        logger.info("sending match report to reporting authority")
        sent_match_report = SentMatchReport.objects.create(to_address=settings.COORDINATOR_EMAIL)
        report_id = sent_match_report.get_report_id()
        sent_match_report.reports.add(*matches)
        sent_match_report.save()
        pdf = PDFMatchReport(matches, identifier).generate_match_report(report_id)
        cls.send_email_to_coordinator(pdf, 'match_delivery', report_id)

    @classmethod
    def send_user_notification(cls, form, notification_name):
        notification = cls.model.objects.on_site().get(name=notification_name)
        preferred_email = form.cleaned_data.get('email')
        to_email = preferred_email
        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
        notification.send(to=[to_email], from_email=from_email)

    @classmethod
    def send_match_notification(cls, user, match_report):
        """Notifies reporting user that a match has been found.
        Requires an NotificationApi.model with `name="match_notification."`

        Args:
          user(User): reporting user
          match_report(MatchReport): MatchReport for which a match has been found
        """
        notification = cls.model.objects.on_site().get(name='match_notification')
        from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
        to = match_report.contact_email
        context = {'report': match_report.report}
        notification.send(to=[to], from_email=from_email, context=context)

    @classmethod
    def send_email_to_coordinator(cls, pdf_to_attach, notification_name, report_id):
        notification = cls.model.objects.on_site().get(name=notification_name)

        to_addresses = [x.strip() for x in settings.COORDINATOR_EMAIL.split(',')]

        email = EmailMultiAlternatives(
            notification.subject,
            notification.render_body_plain(),
            cls.from_email,
            to_addresses)
        email.attach_alternative(notification.render_body(), "text/html")

        gpg = gnupg.GPG()
        school_public_key = settings.COORDINATOR_PUBLIC_KEY
        imported_keys = gpg.import_keys(school_public_key)
        # TODO: sign encrypted doc https://github.com/SexualHealthInnovations/callisto-core/issues/32
        attachment = gpg.encrypt(pdf_to_attach, imported_keys.fingerprints[0], armor=True, always_trust=True)

        email.attach(cls.report_filename.format(report_id), attachment.data, "application/octet-stream")

        email.send()
