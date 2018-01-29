from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from callisto_core.accounts.forms import ReportingVerificationEmailForm
from callisto_core.accounts.models import Account
from callisto_core.accounts.tokens import StudentVerificationTokenGenerator
from callisto_core.accounts.views import SignupView
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)
from callisto_core.utils.api import NotificationApi
from callisto_core.utils.sites import TempSiteID
from callisto_core.wizard_builder.models import Page, SingleLineText

User = get_user_model()


class AccountsTestCase(ReportFlowTestCase):

    def _setup_user(self, *args, **kwargs):
        pass


class SignupViewIntegratedTest(AccountsTestCase):
    signup_url = reverse('signup')
    DEFAULT_POST = {
        'username': 'test',
        'password1': 'p@ssw0rd',
        'password2': 'p@ssw0rd',
        'terms': 'true',
    }

    def test_signup_page_renders_signup_template(self):
        response = self.client.get(self.signup_url)
        self.assertTemplateUsed(response, 'callisto_core/accounts/signup.html')

    def test_displays_signup_form(self):
        response = self.client.get(self.signup_url)
        self.assertIsInstance(response.context['form'], UserCreationForm)
        self.assertContains(response, 'name="password2"')

    def test_displays_signup_form_without_errors_initially(self):
        response = self.client.get(self.signup_url)
        form = response.context['form']
        self.assertEqual(form.errors, {})

    def test_password_fields_must_match(self):
        response = self.client.post(
            self.signup_url,
            {
                'username': 'test',
                'password1': 'p@ssw0rd',
                'password2': 'p@ssw0rd3',
            },
        )
        self.assertFalse(response.context['form'].is_valid())

    def test_user_gets_logged_in_after_signup(self):
        response = self.client.post(
            self.signup_url,
            self.DEFAULT_POST,
        )
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_redirects_to_next(self):
        response = self.client.post(
            self.signup_url + '?next=' + reverse('report_new'),
            self.DEFAULT_POST,
        )
        self.assertRedirects(response, reverse('report_new'))

    def test_accepts_optional_email(self):
        self.client.post(
            self.signup_url,
            {
                'username': 'test',
                'email': 'test@email.co.uk',
                'password1': 'p@ssw0rd',
                'password2': 'p@ssw0rd',
                'terms': 'true',
            },
        )
        self.assertEqual(
            User.objects.get(username='test').email,
            'test@email.co.uk',
        )

    def test_newly_created_user_has_valid_account(self):
        self.client.post(self.signup_url, self.DEFAULT_POST)
        user = User.objects.get(username='test')
        self.assertIsNotNone(user.account)
        self.assertFalse(user.account.is_verified)
        self.assertFalse(user.account.invalid)

    def test_sets_site_id(self):
        temp_site_id = 3
        Site.objects.create(id=temp_site_id)
        with TempSiteID(temp_site_id):
            response = self.client.post(self.signup_url, self.DEFAULT_POST)
            self.assertIn(response.status_code, self.valid_statuses)
            self.assertEqual(
                User.objects.get(username='test').account.site_id,
                temp_site_id,
            )

    def test_signup_disabled_doesnt_create_user(self):
        temp_site_id = 2
        Site.objects.create(id=temp_site_id)
        with TempSiteID(temp_site_id):
            response = self.client.post(self.signup_url, self.DEFAULT_POST)
            self.assertFalse(User.objects.filter(username='test'))

    @override_settings(SITE_ID=2)
    def test_disable_signup_redirects_from_signup(self):
        Site.objects.create(id=2)
        response = self.client.get(self.signup_url)
        self.assertRedirects(response, reverse('login'))


class SignupViewUnitTest(AccountsTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()
        self.request.session = self.client.session
        self.request.META['HTTP_HOST'] = 'testserver'
        self.request.POST = {
            'username': 'test',
            'password1': 'p@ssw0rd',
            'password2': 'p@ssw0rd',
            'terms': 'true',
        }
        self.request.site = Site.objects.first()
        self.request.method = 'POST'

    def test_redirects_to_dashboard(self):
        response = SignupView.as_view()(self.request)
        self.assertEqual(response.get('location'), reverse('dashboard'))

    def test_redirects_to_next(self):
        self.request.GET['next'] = reverse('report_new')

        response = SignupView.as_view()(self.request)
        self.assertEqual(response.get('location'), reverse('report_new'))


class LoginViewTest(AccountsTestCase):
    login_url = reverse('login')

    def test_login_page_renders_login_template(self):
        response = self.client.get(self.login_url)
        self.assertTemplateUsed(response, 'callisto_core/accounts/login.html')

    def test_displays_login_form(self):
        response = self.client.get(self.login_url)
        self.assertIsInstance(response.context['form'], AuthenticationForm)

    def test_user_login_basic_case(self):
        auth_info = {
            'username': 'test',
            'password': 'p@ssw0rd',
        }
        user = User.objects.create_user(**auth_info)
        Account.objects.create(user=user, site_id=1)
        self.client.post(self.login_url, auth_info)

        self.assertTrue(get_user(self.client).is_authenticated)

    def test_user_login_blocked_for_other_sites(self):
        auth_info = {
            'username': 'test',
            'password': 'p@ssw0rd',
        }
        user = User.objects.create_user(**auth_info)
        Account.objects.create(user=user, site_id=2)
        self.client.post(self.login_url, auth_info)

        self.assertFalse(get_user(self.client).is_authenticated)

    def test_login_login_for_non_default_site(self):
        auth_info = {
            'username': 'test',
            'password': 'p@ssw0rd',
        }
        user = User.objects.create_user(**auth_info)
        Account.objects.create(user=user, site_id=2)
        with TempSiteID(2):
            Site.objects.create(id=2)
            self.client.post(self.login_url, auth_info)

        self.assertTrue(get_user(self.client).is_authenticated)

    def test_disable_signups_has_special_instructions(self):
        with TempSiteID(2):
            Site.objects.create(id=2)
            response = self.client.get(self.login_url)
        self.assertIsInstance(response.context['form'], AuthenticationForm)
        self.assertContains(response, 'You should have gotten an email')


class StudentVerificationTest(AccountsTestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='username',
            password='password',
        )
        Account.objects.create(
            user=self.user,
            site_id=1,
            school_email='tech@projectcallisto.org',
        )
        self.client.login(
            username='username',
            password='password',
        )
        with TempSiteID(1):
            self.client_post_report_creation()
        self.verify_url = reverse(
            'reporting_email_confirmation',
            kwargs={'uuid': self.report.uuid},
        )

    def test_verification_get(self):
        response = self.client.get(self.verify_url, follow=True)
        self.assertIsInstance(
            response.context['form'],
            ReportingVerificationEmailForm,
        )

    @override_settings(DEBUG=True)
    def test_verification_post(self):
        response = self.client.post(
            self.verify_url,
            data={'email': 'test@projectcallisto.org'},
            follow=True,
        )
        self.assertTemplateUsed(
            response, 'callisto_core/accounts/school_email_sent.html')

    def test_verification_get_confirmation(self):
        self.user.account.refresh_from_db()
        self.assertFalse(self.user.account.is_verified)
        uidb64 = urlsafe_base64_encode(
            force_bytes(self.user.pk)).decode("utf-8")
        token = StudentVerificationTokenGenerator().make_token(self.user)
        self.client.get(reverse(
            'reporting_email_confirmation',
            kwargs={
                'uidb64': uidb64,
                'token': token,
                'uuid': self.report.uuid,
            },
        ))
        self.user.account.refresh_from_db()
        self.assertTrue(self.user.account.is_verified)
