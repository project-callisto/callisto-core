from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from callisto_core.notification.models import EmailNotification

from ..delivery import models

User = get_user_model()


class ReportAssertionHelper(object):

    def assert_report_exists(self):
        return bool(models.Report.objects.filter(pk=self.report.pk).count())

    def match_report_email_assertions(self):
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'match_confirmation')
        self.assertEqual(message.to, ['test@example.com'])


class ReportPostHelper(object):
    valid_statuses = [200, 301, 302]
    username = 'demo'
    password = 'demo'

    def client_post_login(self):
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        url = reverse('index')
        data = {
            'username': self.username,
            'password': self.password,
        }
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_get_report_creation(self):
        url = reverse('report_new')
        response = self.client.get(url)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_report_creation(self):
        self.client_get_report_creation()
        url = reverse('report_new')
        data = {
            'key': self.passphrase,
            'key_confirmation': self.passphrase,
        }
        response = self.client.post(url, data, follow=True)
        self.report = response.context['report']
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_get_report_delete(self):
        url = reverse(
            'report_delete',
            kwargs={'uuid': self.report.uuid},
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_report_delete(self):
        self.client_get_report_delete()
        url = reverse(
            'report_delete',
            kwargs={'uuid': self.report.uuid},
        )
        data = {'key': self.passphrase}
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_get_report_pdf_view(self):
        url = reverse(
            'report_pdf_view',
            kwargs={'uuid': self.report.uuid},
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_answer_question(self):
        url = reverse(
            'report_update',
            kwargs={'uuid': self.report.uuid, 'step': '0'},
        )
        data = {'question_3': 'blanket ipsum pillowfight'}
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_report_access(self, url):
        response = self.client.post(
            url,
            data={
                'key': self.passphrase,
            },
            follow=True,
        )
        self.assertIn(response.status_code, self.valid_statuses)
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
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_get_matching_enter_empty(self):
        url = reverse(
            'reporting_matching_enter',
            kwargs={'uuid': self.report.uuid},
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_matching_enter_empty(self):
        self.client_get_matching_enter_empty()
        url = reverse(
            'reporting_matching_enter',
            kwargs={'uuid': self.report.uuid},
        )
        data = {'identifier': ''}
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_get_matching_enter(self):
        url = reverse(
            'matching_enter',
            kwargs={'uuid': self.report.uuid},
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_matching_withdraw(self):
        url = reverse(
            'report_matching_withdraw',
            kwargs={'uuid': self.report.uuid},
        )
        data = {'key': self.passphrase}
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_matching_enter(
            self, identifier='https://www.facebook.com/callistoorg'):
        url = reverse(
            'matching_enter',
            kwargs={'uuid': self.report.uuid},
        )
        data = {'identifier': identifier}
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, self.valid_statuses)
        return response

    def client_post_reporting_confirmation(self):
        response = self.client.post(
            reverse(
                'reporting_confirmation',
                kwargs={'uuid': self.report.uuid},
            ),
            data={
                'confirmation': True,
                'key': self.passphrase,
            },
            follow=True,
        )
        self.assertIn(response.status_code, self.valid_statuses)
        return response


class ReportFlowHelper(
    TestCase,
    ReportPostHelper,
    ReportAssertionHelper,
):
    passphrase = 'super secret'
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

    def client_clear_passphrase(self):
        session = self.client.session
        session['passphrases'] = {}
        session.save()
        self.assertEqual(
            self.client.session.get('passphrases'),
            {},
        )

    def client_set_passphrase(self):
        session = self.client.session
        passphrases = session.get('passphrases', {})
        passphrases[str(self.report.uuid)] = self.passphrase
        session['passphrases'] = passphrases
        session.save()
