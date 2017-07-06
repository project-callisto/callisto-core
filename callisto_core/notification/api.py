import logging

import gnupg
import pytz

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone

from ..delivery.models import SentMatchReport
from ..delivery.report_delivery import PDFFullReport, PDFMatchReport
from .models import EmailNotification

logger = logging.getLogger(__name__)
tzname = settings.REPORT_TIME_ZONE or 'America/Los_Angeles'
timezone.activate(pytz.timezone(tzname))


class CallistoCoreNotificationApi(object):

    model = EmailNotification
    report_filename = "report_{0}.pdf.gpg"
    from_email = '"Reports" <reports@{0}>'.format(settings.APP_URL)

    @classmethod
    def get_user_site(cls, user):
        '''Takes in a user model, and should return a site

        example:
            for an Account model 1 to 1 with User that has a site attribute
            return user.account.site
        '''
        return None

    # TODO: create a PDFGenerationApi https://github.com/SexualHealthInnovations/callisto-core/issues/150
    # TODO (cont): remove this method, make it a attribute
    @classmethod
    def get_report_title(cls):
        return 'Report'

    @classmethod
    def get_cover_page(cls, *args, **kwargs):
        return []

    @classmethod
    def send(cls, notification, attachments):
        pass

    @classmethod
    def send_report_to_authority(cls, sent_full_report, decrypted_report, site_id=None):
        logger.info("sending report to reporting authority")
        pdf_report_id = sent_full_report.get_report_id()
        sent_full_report.report.submitted_to_school = timezone.now()
        # TODO: create a PDFGenerationApi https://github.com/SexualHealthInnovations/callisto-core/issues/150
        pdf = PDFFullReport(sent_full_report.report, decrypted_report).generate_pdf_report(pdf_report_id)
        cls.send_email_to_authority_intake(pdf, 'report_delivery', pdf_report_id, site_id)
        # save report timestamp only if generation & email work
        sent_full_report.report.save()

    @classmethod
    def send_matching_report_to_authority(cls, matches, identifier):
        """ Encrypts the generated PDF with GPG and attaches it to an email to the reporting authority """
        # assume all matches are on the same site
        user = matches[0].report.owner
        site = cls.get_user_site(user)
        logger.info("sending match report to reporting authority")
        sent_match_report = SentMatchReport.objects.create(to_address=settings.COORDINATOR_EMAIL)
        report_id = sent_match_report.get_report_id()
        sent_match_report.reports.add(*matches)
        sent_match_report.save()
        # TODO: create a PDFGenerationApi https://github.com/SexualHealthInnovations/callisto-core/issues/150
        pdf = PDFMatchReport(matches, identifier).generate_match_report(report_id)
        cls.send_email_to_authority_intake(pdf, 'match_delivery', report_id, site_id=site.id)

    @classmethod
    def send_user_notification(cls, form, notification_name, site_id=None):
        site = Site.objects.get(id=site_id)
        notification = cls.model.objects.on_site(site_id).get(name=notification_name)
        preferred_email = form.cleaned_data.get('email')
        to_email = preferred_email
        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
        context = {'domain': site.domain}
        notification.send(to=[to_email], from_email=from_email, context=context)

    @classmethod
    def send_match_notification(cls, user, match_report):
        """Notifies reporting user that a match has been found.
        Requires an NotificationApi.model with `name="match_notification."`

        Args:
          user(User): reporting user
          match_report(MatchReport): MatchReport for which a match has been found
        """
        site = cls.get_user_site(user)
        notification = cls.model.objects.on_site(site.id).get(name='match_notification')
        from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
        to = match_report.contact_email
        context = {'report': match_report.report, 'domain': site.domain}
        notification.send(to=[to], from_email=from_email, context=context)

    @classmethod
    def send_email_to_authority_intake(cls, pdf_to_attach, notification_name, report_id, site_id=None):
        site = Site.objects.get(id=site_id)
        context = {'domain': site.domain}
        notification = cls.model.objects.on_site(site_id).get(name=notification_name)

        to_addresses = [x.strip() for x in settings.COORDINATOR_EMAIL.split(',')]

        email = EmailMultiAlternatives(
            notification.subject,
            notification.render_body(context),
            cls.from_email,
            to_addresses)

        gpg = gnupg.GPG()
        authority_public_key = settings.COORDINATOR_PUBLIC_KEY
        imported_keys = gpg.import_keys(authority_public_key)
        # TODO: sign encrypted doc https://github.com/SexualHealthInnovations/callisto-core/issues/32
        attachment = gpg.encrypt(pdf_to_attach, imported_keys.fingerprints[0], armor=True, always_trust=True)

        email.attach(cls.report_filename.format(report_id), attachment.data, "application/octet-stream")

        email.send()
