import logging
import typing

import gnupg

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.utils import timezone

from callisto_core.reporting.report_delivery import (
    PDFFullReport, PDFMatchReport,
)

logger = logging.getLogger(__name__)


class CallistoCoreNotificationApi(object):

    report_filename = "report_{0}.pdf.gpg"
    report_title = 'Report'

    # utilities

    @property
    def from_email(self):
        return '"Reports" <reports@{0}>'.format(self.mail_domain)

    @property
    def mail_domain(_):
        return settings.APP_URL

    @property
    def model(_):
        from callisto_core.notification.models import EmailNotification
        return EmailNotification

    def get_cover_page(self, *args, **kwargs):
        '''TODO: create pdf api, move this there'''
        return []

    def user_site_id(self, user):
        '''
        Redefine this method and change the value of 1 to the user's site id

        examples:
            # for an Account model 1 to 1 with User that has a site attribute
            user.account.site.id

            # for a setup that utilizes settings.SITE_ID
            settings.SITE_ID
        '''
        return 1

    def split_addresses(self, addresses):
        if isinstance(addresses, str):
            return [x.strip() for x in addresses.split(',')]
        else:
            return addresses

    # entrypoints

    def slack_notification(self, msg, channel):
        pass

    def send_account_activation_email(self, *args, **kwargs):
        pass

    def send_report_to_authority(
        self,
        sent_report,
        to_addresses: typing.List[str],
        report_data: dict,
        public_key: str,
        site_id=0,
    ) -> None:
        '''
        Send new full report to the reporting coordinator

        Called at the end of the "reporting" flow
        '''
        self.context = {
            'notification_name': 'report_delivery',
            'to_addresses': to_addresses,
            'site_id': site_id,
        }
        self.notification_with_full_report(
            sent_report, report_data, public_key, to_addresses)
        self.send()

        # TODO: re-evaluate this decision
        # save report timestamp only if generation & email work
        sent_report.report.submitted_to_school = timezone.now()
        sent_report.report.save()

    def send_confirmation(
        self,
        email_type: str,
        to_addresses: typing.List[str],
        site_id=0,
    ) -> None:
        '''
        Send a matching or submission confirmation email to the user

        email_type default valid options:
            'match_confirmation'
            'submit_confirmation'

        Called if an email confirmation is requested
        '''
        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(
            self.mail_domain,
        )
        self.context = {
            'notification_name': email_type,
            'to_addresses': to_addresses,
            'site_id': site_id,
            'from_email': from_email,
        }
        self.send()

    def send_matching_report_to_authority(
        self,
        matches: list,
        identifier: str,
        to_addresses: typing.List[str],
        public_key: str,
    ):
        '''
        Notifies coordinator that a match has been found

        Assumes all matches are on the same site

        Called during a successful matching run
        '''
        user = matches[0].report.owner

        self.context = {
            'notification_name': 'match_delivery',
            'to_addresses': to_addresses,
            'site_id': self.user_site_id(user),
            'user': user,
        }
        self.notification_with_match_report(
            matches, identifier, to_addresses, public_key)
        self.send()

    def send_match_notification(self, match_report):
        '''
        Notifies reporting user that a match has been found.

        Called during a successful matching run

        Args:
            user(User): reporting user
            match_report(MatchReport): MatchReport for which
                a match has been found
        '''
        from_email = '"Callisto Matching" <notification@{0}>'.format(
            self.mail_domain,
        )
        user = match_report.report.owner

        self.context = {
            'notification_name': 'match_notification',
            'to_addresses': [match_report.report.contact_email],
            'site_id': self.user_site_id(user),
            'from_email': from_email,
            'report': match_report.report,
            'user': user,
        }
        self.send()

    # report attachment
    # TODO: write to self.attachment without dict.update

    def notification_with_full_report(
        self,
        sent_report,
        report_data,
        public_key,
        to_addresses,
    ):
        report_id = sent_report.get_report_id()
        report_pdf_class = PDFFullReport(sent_report.report, report_data)
        report_file = report_pdf_class.generate_pdf_report(
            report_id, to_addresses)

        self._notification_with_report(report_id, report_file, public_key)

    def notification_with_match_report(
        self,
        matches,
        identifier,
        to_addresses,
        public_key,
    ):
        # TODO: make match notification_with_full_report more closely
        from callisto_core.delivery.models import SentMatchReport
        sent_match_report = SentMatchReport.objects.create(
            to_address=self.context['to_addresses'][0],
        )
        sent_match_report.reports.add(*matches)
        sent_match_report.save()

        report_id = sent_match_report.get_report_id()
        report_pdf = PDFMatchReport(matches, identifier)
        report_file = report_pdf.generate_match_report(report_id, to_addresses)

        self._notification_with_report(report_id, report_file, public_key)

    def _notification_with_report(self, report_id, report_file, public_key):
        report_file = self._encrypt_file(report_file, public_key)
        attachment = (
            self.report_filename.format(report_id),
            report_file,
            "application/octet-stream",
        )
        self.context.update({'attachment': attachment})

    def _encrypt_file(self, file_data, public_key):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(public_key)
        return gpg.encrypt(
            file_data,
            imported_keys.fingerprints[0],
            armor=True,
            always_trust=True,
        ).data

    # send cycle
    # TODO: make self.send execute async
    # TODO: pass context as an arguement to send? (will help with async calls)
    # TODO: tests a spec for pre / post (so they don't get deleted)

    def pre_send(self):
        self.set_domain()
        self.set_notification()
        self.render_body()

    def send(self):
        '''
        required:
            self.context.
                site_id
                notification_name
                to_addresses
        optional:
            self.context.
                from_email
                attachment
        '''
        self.pre_send()
        self.send_email()
        self.post_send()

    def post_send(self):
        self.log_action()

    # send cycle implementation

    def set_domain(self):
        from django.contrib.sites.models import Site
        if not self.context.get('domain'):
            site = Site.objects.get(id=self.context.get('site_id'))
            self.context.update({'domain': site.domain})

    def set_notification(self):
        site_id = self.context.get('site_id')
        name = self.context['notification_name']
        notifications = self.model.objects.on_site(site_id).filter(name=name)
        if len(notifications) != 1:
            logger.warn(
                f'too many results for {self.model.__name__}(site_id={site_id}, name={name})')
        notification = notifications[0]
        self.context.update({
            'subject': notification.subject,
            'body': notification.body,
        })

    def render_body(self):
        body_template = Template(self.context['body'])
        body_context = Context(self.context)
        body_rendered = body_template.render(body_context)
        self.context.update({'body': body_rendered})

    def send_email(self):
        email = EmailMessage(
            subject=self.context['subject'],
            body=self.context['body'],
            from_email=self.context.get('from_email', self.from_email),
            to=self.split_addresses(self.context['to_addresses']),
        )
        if self.context.get('attachment'):
            email.attach(*self.context.get('attachment'))
        email.send(fail_silently=False)
        self.context.update({'EmailMessage': email})

    def log_action(self):
        logger.info('notification.send(subject={}, name={})'.format(
            self.context['subject'],
            self.context['notification_name'],
        ))
