import logging
import typing

import gnupg

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.utils import timezone

from callisto_core.reporting.report_delivery import PDFFullReport, PDFMatchReport

logger = logging.getLogger(__name__)


class CallistoCoreNotificationApi(object):

    report_filename = "report_{0}.pdf.gpg"
    from_email = '"Reports" <reports@{0}>'.format(settings.APP_URL)
    report_title = 'Report'

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

    def to_coordinators(self):
        return [x.strip() for x in settings.COORDINATOR_EMAIL.split(',')]

    # entrypoints

    def send_report_to_authority(
        self,
        sent_report,
        report_data: dict,
        site_id=0,
    ) -> None:
        '''
        Send new full report to the reporting coordinator

        Called at the end of the "reporting" flow
        '''
        self.context = {
            'notification_name': 'report_delivery',
            'to_addresses': self.to_coordinators(),
            'site_id': site_id,
        }
        self.notification_with_full_report(sent_report, report_data)
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
            settings.APP_URL,
        )
        self.context = {
            'notification_name': email_type,
            'to_addresses': to_addresses,
            'site_id': site_id,
            'from_email': from_email,
        }
        self.send()

    def send_matching_report_to_authority(self, matches, identifier):
        '''
        Notifies coordinator that a match has been found

        Assumes all matches are on the same site

        Called during a successful matching run
        '''
        user = matches[0].report.owner

        self.context = {
            'notification_name': 'match_delivery',
            'to_addresses': self.to_coordinators(),
            'site_id': self.user_site_id(user),
            'user': user,
        }
        self.notification_with_match_report(matches, identifier)
        self.send()

    def send_match_notification(self, user, match_report):
        '''
        Notifies reporting user that a match has been found.

        Called during a successful matching run

        Args:
            user(User): reporting user
            match_report(MatchReport): MatchReport for which
                a match has been found
        '''
        from_email = '"Callisto Matching" <notification@{0}>'.format(
            settings.APP_URL,
        )

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

    def notification_with_full_report(self, sent_report, report_data):
        report_id = sent_report.get_report_id()
        report_file = PDFFullReport(
            sent_report.report, report_data
        ).generate_pdf_report(report_id)

        self._notification_with_report(report_id, report_file)

    def notification_with_match_report(self, matches, identifier):
        # TODO: make match notification_with_full_report more closely
        from callisto_core.delivery.models import SentMatchReport
        sent_match_report = SentMatchReport.objects.create(
            to_address=self.context['to_addresses'][0],
        )
        sent_match_report.reports.add(*matches)
        sent_match_report.save()

        report_id = sent_match_report.get_report_id()
        report_pdf = PDFMatchReport(matches, identifier)
        report_file = report_pdf.generate_match_report(report_id)

        self._notification_with_report(report_id, report_file)

    def _notification_with_report(self, report_id, report_file):
        report_file = self._encrypt_file(report_file)
        attachment = (
            self.report_filename.format(report_id),
            report_file,
            "application/octet-stream",
        )
        self.context.update({'attachment': attachment})

    def _encrypt_file(self, file_data):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(settings.COORDINATOR_PUBLIC_KEY)
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
        # TODO: seperate funcs for getting notification and assigning values
        notification = self.model.objects.on_site(
            self.context.get('site_id'),
        ).get(name=self.context['notification_name'])
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
            to=self.context['to_addresses'],
        )
        if self.context.get('attachment'):
            email.attach(*self.context.get('attachment'))
        email.send()
        self.context.update({'EmailMessage': email})

    def log_action(self):
        logger.info('notification.send(subject={}, name={})'.format(
            self.context['subject'],
            self.context['notification_name'],
        ))
