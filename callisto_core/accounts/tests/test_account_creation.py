from unittest import skip

from django_migration_testcase import MigrationTest

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)
from callisto_core.utils.api import NotificationApi

from ..models import Account, BulkAccount

User = get_user_model()


class AccountEmailParsingTest(ReportFlowTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Site.objects.create(id=2)
        BulkAccount.objects.create(
            emails='tech@projectcallisto.org',
            site_id=2,
        )

    def test_case_lowered(self):
        BulkAccount.objects.create(
            emails='TECH@projectcallisto.org',
            site_id=2,
        )
        self.assertEqual(Account.objects.filter(
            school_email='TECH@projectcallisto.org').count(), 0)
        self.assertEqual(Account.objects.filter(
            school_email='tech@projectcallisto.org').count(), 1)

    def test_empty_emails_not_sent(self):
        bulk_account = BulkAccount.objects.create(
            emails=' , ',
            site_id=2,
        )

        self.assertEqual(
            bulk_account.parsed_emails,
            ['', '']
        )

    def test_email_address_is_user_name(self):
        BulkAccount.objects.create(
            emails='tech@projectcallisto.org',
            site_id=2,
        )

        self.assertTrue(
            User.objects.filter(username='tech@projectcallisto.org').count(),
        )

    def test_spaces_allowed_in_email_list(self):
        bulk_account = BulkAccount.objects.create(
            emails='first@example.com,  second@example.com',
            site_id=2,
        )

        self.assertEqual(
            bulk_account.parsed_emails,
            ['first@example.com', 'second@example.com']
        )

    def test_special_characters_allowed_in_email(self):
        bulk_account = BulkAccount.objects.create(
            emails='first!?#$%^&*@example.com',
            site_id=2,
        )

        self.assertEqual(
            bulk_account.parsed_emails,
            ['first!?#$%^&*@example.com']
        )

    def test_basic_case(self):
        bulk_account = BulkAccount.objects.create(
            emails='first@example.com,second@example.com,third@example.com',
            site_id=2,
        )

        self.assertEqual(
            bulk_account.parsed_emails,
            ['first@example.com', 'second@example.com', 'third@example.com']
        )

    def test_can_run_multiple_times_on_one_account(self):
        bulk_account = BulkAccount.objects.create(
            emails='first@example.com',
            site_id=2,
        )
        self.assertEqual(
            bulk_account.parsed_emails,
            ['first@example.com']
        )

        bulk_account = BulkAccount.objects.create(
            emails='first@example.com',
            site_id=2,
        )
        self.assertEqual(
            bulk_account.parsed_emails,
            ['first@example.com']
        )


class AccountEmailTest(ReportFlowTestCase):

    @skip('skip pending NotificationApi update')
    def test_gets_account_activation_email(self):
        BulkAccount.objects.create(
            emails='tech@projectcallisto.org',
            site_id=2,
        )
        self.assertEqual(len(self.cassette), 1)
        self.assertEqual(
            self.cassette.requests[0].uri,
            NotificationApi.mailgun_post_route,
        )

    def test_can_activate_account(self):
        BulkAccount.objects.create(
            emails='tech@projectcallisto.org',
            site_id=2,
        )
        account = Account.objects.get(school_email='tech@projectcallisto.org')
        uid = urlsafe_base64_encode(
            force_bytes(account.user.pk)).decode("utf-8")
        token = default_token_generator.make_token(account.user)

        response = self.client.get(
            reverse(
                'activate_account',
                kwargs={'uidb64': uid, 'token': token},
            ),
            follow=True,
        )

        self.assertNotIn('invalid_token', response.context)
        self.assertTemplateUsed(
            response, 'callisto_core/accounts/account_activation_confirm.html')
