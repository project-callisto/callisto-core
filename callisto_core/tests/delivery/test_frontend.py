from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
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


@override_settings(
    DEBUG=True,
    SITE_ID=1,
)
class FrontendTestCase(
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
        cls.setup_site()
        cls.setup_user()
        cls.create_report()

    @classmethod
    def setup_browser(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument("--disable-gpu")
        cls.browser = webdriver.Chrome(
            chrome_options=chrome_options,
        )

    @classmethod
    def setup_user(cls):
        User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.browser.get(cls.live_server_url)
        ElementHelper(cls.browser).enter_username()
        ElementHelper(cls.browser).enter_password()
        ElementHelper(cls.browser).submit()

    @classmethod
    def create_report(cls):
        cls.browser.get(cls.live_server_url + reverse('report_new'))
        ElementHelper(cls.browser).enter_key()
        ElementHelper(cls.browser).enter_key_confirmation()
        ElementHelper(cls.browser).submit()
        cls.report = Report.objects.first()

    @classmethod
    def setup_site(cls):
        port = urlparse(cls.live_server_url).port
        Site.objects.filter(id=1).update(domain='localhost:{}'.format(port))
        cls.site = Site.objects.filter(id=1)

    def setUp(self):
        super().setUp()
        url = reverse(
            'report_update',
            kwargs={'uuid': self.report.uuid, 'step': 0}
        )
        self.browser.get(self.live_server_url + url)


@override_settings(
    DEBUG=True,
    SITE_ID=1,
)
class EncryptedFrontendTest(
    FrontendTestCase,
):
    pass
