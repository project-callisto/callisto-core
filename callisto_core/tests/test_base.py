from callisto_core.notification.models import EmailNotification

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..delivery import models

User = get_user_model()


class ReportAssertionHelper(object):

    def assert_report_exists(self):
        return bool(models.Report.objects.filter(pk=self.report.pk).count())

    def match_report_email_assertions(self):
        self.assertEqual(len(mail.outbox), 3)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test1@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[1]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test2@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[2]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertIn('"Reports" <reports@', message.from_email)
        self.assertIn('test match delivery body', message.body)
        self.assertRegexpMatches(
            message.attachments[0][0],
            'report_.*\\.pdf\\.gpg')


class ReportPostHelper(object):

    def client_post_report_creation(self):
        response = self.client.post(
            reverse('report_new'),
            data={
                'key': self.secret_key,
                'key_confirmation': self.secret_key,
            },
            follow=True,
        )
        self.report = response.context['report']
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_get_report_delete(self):
        response = self.client.get(
            reverse(
                'report_delete',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_get_report_view_pdf(self):
        response = self.client.get(
            reverse(
                'report_view_pdf',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_question_answer(self, url, answer):
        response = self.client.post(
            url,
            data=answer,
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_report_access(self, url):
        response = self.client.post(
            url,
            data={
                'key': self.secret_key,
            },
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_report_prep(self):
        response = self.client.post(
            reverse(
                'reporting_prep',
                kwargs={'uuid': self.report.uuid},
            ),
            data={
                'contact_email': 'test@example.com',
                'contact_phone': '555-555-5555',
            },
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_matching_enter_empty(self):
        response = self.client.post(
            reverse(
                'report_matching_enter',
                kwargs={'uuid': self.report.uuid},
            ),
            data={
                'identifier': '',
            },
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_matching_enter(self):
        response = self.client.post(
            reverse(
                'report_matching_enter',
                kwargs={'uuid': self.report.uuid},
            ),
            data={
                'identifier': 'https://www.facebook.com/callistoorg',
            },
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response

    def client_post_reporting_confirmation(self):
        response = self.client.post(
            reverse(
                'reporting_confirmation',
                kwargs={'uuid': self.report.uuid},
            ),
            data={
                'confirmation': True,
                'key': self.secret_key,
            },
            follow=True,
        )
        self.assertIn(response.status_code, [200, 301, 302])
        return response


class ReportFlowHelper(
    TestCase,
    ReportPostHelper,
    ReportAssertionHelper,
):
    secret_key = 'super secret'
    fixtures = [
        'wizard_builder_data',
        'callisto_core_notification_data',
    ]

    def setUp(self):
        self._setup_sites()
        self._setup_user()

    def _setup_user(self):
        self.user = User.objects.create_user(
            username='testing_122',
            password='testing_12',
        )
        self.client.login(
            username='testing_122',
            password='testing_12',
        )

    def _setup_sites(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()

    def client_clear_secret_key(self):
        session = self.client.session
        session['secret_key'] = None
        session.save()
        self.assertEqual(
            self.client.session.get('secret_key'),
            None,
        )
