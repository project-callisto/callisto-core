from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test.utils import override_settings

from callisto_core.accounts.forms import ReportingVerificationEmailForm
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)
from callisto_core.utils.api import TenantApi

User = get_user_model()


class StudentVerificationTest(ReportFlowTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()
        self.request.method = 'POST'
        self.request.META['HTTP_HOST'] = 'testserver'

    def test_projectcallisto_not_accepted(self):
        form = ReportingVerificationEmailForm(
            {'email': 'myname@projectcallisto.org'},
            school_email_domain='example.com',
        )
        self.assertFalse(form.is_valid())

    def test_subdomain_not_accepted(self):
        form = ReportingVerificationEmailForm(
            {'email': 'myname@cats.example.com'},
            school_email_domain='example.com',
        )
        self.assertFalse(form.is_valid())

    def test_domain_match_on_username_not_accepted(self):
        form = ReportingVerificationEmailForm(
            {'email': 'example.com@gmail.com'},
            school_email_domain='example.com',
        )
        self.assertFalse(form.is_valid())

    def test_non_email_rejected(self):
        form = ReportingVerificationEmailForm(
            {'email': 'notanemail'},
            school_email_domain='example.com',
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['email'],
            ['Enter a valid email address.']
        )

    def test_control(self):
        form = ReportingVerificationEmailForm(
            {'email': 'hello@example.com'},
            school_email_domain='example.com',
        )
        self.assertTrue(form.is_valid())

    @override_settings(DEBUG=True)
    def test_control_with_debug(self):
        form = ReportingVerificationEmailForm(
            {'email': 'hello@example.com'},
            school_email_domain='example.com',
        )
        self.assertTrue(form.is_valid())

    def test_multiple_domains(self):
        form = ReportingVerificationEmailForm(
            {'email': 'hello@cats.com'},
            school_email_domain='example.com,cats.com,dogs.com',
        )
        self.assertTrue(form.is_valid())

    def test_empty_domain_allowed(self):
        form = ReportingVerificationEmailForm(
            {'email': 'hello@cats.com'},
            school_email_domain='',
        )
        self.assertTrue(form.is_valid())
