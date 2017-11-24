from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from callisto_core.delivery.models import Report
from wizard_builder.tests import test_frontend as wizard_builder_tests

User = get_user_model()


class AuthMixin:
    passphrase = 'soooooo seekrit'
    username = 'demo'
    password = 'demo'


class ElementHelper(
    wizard_builder_tests.ElementHelper,
    AuthMixin,
):

    def enter_key(self):
        self.browser.find_element_by_css_selector(
            '[name="key"]').send_keys(self.passphrase)

    def enter_key_confirmation(self):
        self.browser.find_element_by_css_selector(
            '[name="key_confirmation"]').send_keys(self.passphrase)

    def submit(self):
        self.browser.find_element_by_css_selector(
            '[type="submit"]').click()

    def enter_username(self):
        self.browser.find_element_by_css_selector(
            '[name="username"]').send_keys(self.password)

    def enter_password(self):
        self.browser.find_element_by_css_selector(
            '[name="password"]').send_keys(self.username)


class __FrontendCase(
    wizard_builder_tests.FrontendTest,
    AuthMixin,
):
    fixtures = [
        'wizard_builder_data',
        'callisto_core_notification_data',
    ]

    @property
    def element(cls):
        return ElementHelper(cls.browser)

    @classmethod
    def setUpClass(cls):
        super(StaticLiveServerTestCase, cls).setUpClass()
        cls.setup_browser()
        cls.setup_data()

    @classmethod
    def setup_browser(cls):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-gpu")
        cls.browser = webdriver.Chrome(
            chrome_options=chrome_options,
        )

    @classmethod
    def setup_data(cls):
        call_command(
            'loaddata',
            *cls.fixtures,
            **{'verbosity': 1, 'database': 'default'},
        )

    def setup_user(self):
        User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        self.browser.get(self.live_server_url)
        self.element.enter_username()
        self.element.enter_password()
        self.element.submit()

    def setup_report(self):
        self.browser.get(self.live_server_url + reverse('report_new'))
        self.element.enter_key()
        self.element.enter_key_confirmation()
        self.element.submit()
        self.report = Report.objects.first()

    def setUp(self):
        super().setUp()
        self.setup_user()
        self.setup_report()
        url = reverse(
            'report_update',
            kwargs={'uuid': self.report.uuid, 'step': 0}
        )
        self.browser.get(self.live_server_url + url)


@override_settings(DEBUG=True)
class EncryptedFrontendTest(
    __FrontendCase,
):
    pass
