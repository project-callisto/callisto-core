from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

User = get_user_model()


class ReportFlowHelper(TestCase):

    secret_key = 'super secret'
    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        self.user = User.objects.create_user(
            username='testing_122',
            password='testing_12',
        )
        self.client.login(
            username='testing_122',
            password='testing_12',
        )
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()

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
        return response

    def client_get_report_delete(self):
        return self.client.get(
            reverse(
                'report_delete',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )

    def client_get_report_view_pdf(self):
        return self.client.get(
            reverse(
                'report_view_pdf',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )

    def client_post_question_answer(self, url, answer):
        return self.client.post(
            url,
            data=answer,
            follow=True,
        )

    def client_post_report_access(self, url):
        return self.client.post(
            url,
            data={
                'key': self.secret_key,
            },
            follow=True,
        )

    def client_clear_secret_key(self):
        session = self.client.session
        session['secret_key'] = None
        session.save()
        self.assertEqual(
            self.client.session.get('secret_key'),
            None,
        )

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
        self.assertRegexpMatches(message.attachments[0][0], 'report_.*\\.pdf\\.gpg')
