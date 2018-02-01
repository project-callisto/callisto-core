import copy
import logging
import os
import typing

import gnupg
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, Spacer

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template import Context, Template
from django.template.loader import get_template
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from callisto_core.notification import tasks
from callisto_core.reporting.report_delivery import (
    PDFFullReport, PDFMatchReport,
)
from callisto_core.utils.api import TenantApi

logger = logging.getLogger(__name__)


class CallistoCoreNotificationApi(object):

    report_filename = "callisto_report_{0}.pdf.gpg"
    report_title = 'Callisto Record'
    logo_path = '../../assets/callisto_logo.png'

    # utilities

    @property
    def ALERT_LIST(self):
        return [
            'tech@projectcallisto.org',
        ]

    @property
    def mail_domain(self):
        return 'mail.callistocampus.org'

    @property
    def model(self):
        from callisto_core.notification.models import EmailNotification
        return EmailNotification

    @property
    def site_id(self):
        return self.context['site_id']

    @property
    def from_email(self):
        return f'"Callisto" <noreply@{self.mail_domain}>'

    def user_site_id(self, user):
        return user.account.site_id

    def split_addresses(self, addresses):
        if isinstance(addresses, str):
            return [x.strip() for x in addresses.split(',')]
        else:
            return addresses

    def get_cover_page(self, report_id, recipient):
        title = f"{self.report_title} No.: {report_id}"

        styles = getSampleStyleSheet()
        headline_style = styles["Heading1"]
        headline_style.alignment = TA_CENTER
        headline_style.fontSize = 48
        subtitle_style = styles["Heading2"]
        subtitle_style.fontSize = 24
        subtitle_style.leading = 26
        subtitle_style.alignment = TA_CENTER

        CoverPage = []
        logo = os.path.join(
            settings.BASE_DIR,
            self.logo_path,
        )

        image = Image(logo, 3 * inch, 3 * inch)
        CoverPage.append(image)
        CoverPage.append(Spacer(1, 18))
        CoverPage.append(Paragraph("CONFIDENTIAL", headline_style))
        CoverPage.append(Spacer(1, 30))
        CoverPage.append(Spacer(1, 40))
        CoverPage.append(Paragraph(title, subtitle_style))
        CoverPage.append(Spacer(1, 40))
        paragraph = Paragraph(
            f"Intended for: {recipient}, Title IX Coordinator", subtitle_style)
        CoverPage.append(paragraph)
        CoverPage.append(PageBreak())
        return CoverPage

    # entrypoints

    def slack_notification(
        self,
        msg: str,  # slack message
        channel='',  # slack channel
        type='',  # for test assertions
    ):
        pass

    def send_with_kwargs(self, **kwargs):
        self.context = {**kwargs}
        self.send()

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
        self.context = {
            'notification_name': email_type,
            'to_addresses': to_addresses,
            'site_id': site_id,
        }
        self.send()

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

    def send_student_verification_email(self, form, *args, **kwargs):
        email = form.cleaned_data.get('email')
        for user in form.get_users(email):
            self.send_with_kwargs(
                site_id=user.account.site_id,
                to_addresses=[email],
                email_subject='Verify your student email',
                email_name='student_verification_email',
                redirect_url=form.redirect_url,
                email_template_name=form.view.email_template_name,
                user=form.view.request.user,
            )

    def send_password_reset_email(self, form, *args, **kwargs):
        email = form.cleaned_data.get('email')
        for user in form.get_users(email):
            self.send_with_kwargs(
                site_id=user.account.site_id,
                to_addresses=[email],
                email_subject='Reset your password',
                email_name='password_reset_email',
                uid=args[2]['uid'],
                protocol=args[2]['protocol'],
                email_template_name=args[1],
                user=args[2]['user'],
                token=args[2]['token'],
            )

    def send_account_activation_email(self, user, email):
        # TODO: mirror send_password_reset_email
        self.send_with_kwargs(
            email_template_name='callisto_core/accounts/account_activation_email.html',
            to_addresses=[email],
            site_id=user.account.site_id,
            user=user,
            uid=urlsafe_base64_encode(
                force_bytes(user.pk)),
            token=default_token_generator.make_token(
                copy.copy(user)),
            email_subject='Keep Our Community Safe with Callisto',
            email_name='account_activation_email',
        )

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
        user = match_report.report.owner
        self.send_with_kwargs(
            notification_name='match_notification',
            to_addresses=[match_report.report.contact_email],
            site_id=self.user_site_id(user),
            report=match_report.report,
            user=user,
        )

    # report attachment

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

    # entrypoint helpers

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

    def pre_send(self):
        self.set_protocol()
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
                attachment
        '''
        self.pre_send()
        self.send_email()
        self.post_send()

    def post_send(self):
        self.log_action()

    # send cycle implementation

    def _extra_data(self):
        '''for tests'''
        return {}

    def _mail_attachments(self):
        files = {'files': []}
        if self.context.get('attachment'):
            file_name = self.context['attachment'][0]
            file_data = self.context['attachment'][1]
            files['files'].append(
                ('attachment', (file_name, file_data)),
            )
        return files

    def set_protocol(self):
        if not self.context.get('protocol'):
            protocol = 'http' if settings.DEBUG else 'https'  # TODO: not this
            self.context.update({'protocol': protocol})

    def set_domain(self):
        self.context.update({'domain': TenantApi.get_current_domain()})

    def render_body(self):
        body_template = Template(self.context['body'])
        body_context = Context(self.context)
        body_rendered = body_template.render(body_context)
        self.context.update({'body': body_rendered})

    def set_notification(self):
        if self.context.get('email_template_name'):
            body = get_template(
                self.context['email_template_name']).template.source
            self.context.update({
                'notification_name': self.context['email_template_name'],
                'subject': self.context['email_subject'],
                'body': body,
            })
        else:
            site_id = self.context.get('site_id')
            name = self.context['notification_name']
            notifications = self.model.objects.on_site(
                site_id).filter(name=name)
            if len(notifications) != 1:
                logger.warn(
                    f'too many results for {self.model.__name__}(site_id={site_id}, name={name})')
            notification = notifications[0]
            self.context.update({
                'subject': notification.subject,
                'body': notification.body,
            })

    def send_email(self):
        email_data = {
            'to': self.context['to_addresses'],
            'subject': self.context['subject'],
            'html': self.context['body'],
            **self._extra_data(),
        }
        task_response = tasks.SendEmail.delay(
            self.mail_domain, email_data, self._mail_attachments())
        self.context.update({'task_id': task_response.task_id})
        """
        self.context.update({
            'response': getattr(response, 'context', response),
            'response_status': response.status_code,
            'response_content': response.content,
        })
        """

    def log_action(self):
        logger.info('notification.send(subject={}, name={})'.format(
            self.context['subject'],
            self.context['notification_name'],
        ))

        if self.context.get('attachment'):
            self.context.update({
                'attachment': (
                    self.context['attachment'][0],
                    'FILEDATA',
                )
            })

        if self.context.get('body'):
            self.context.update({
                'body': self.context['body'][:80]
            })
        """
        if not self.context.get('response_status') == 200:
            logger.error(f'status_code!=200, context: {self.context}')
        """
