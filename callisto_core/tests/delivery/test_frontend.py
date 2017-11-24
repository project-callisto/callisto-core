from django.contrib.auth import get_user_model

from wizard_builder.tests import test_frontend as wizard_builder_tests

User = get_user_model()


class PassphraseMixin:
    passphrase = 'soooooo seekrit'


class ElementHelper(
    wizard_builder_tests.ElementHelper,
    PassphraseMixin,
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


class FrontendTestCase(
    wizard_builder_tests.FrontendTest,
    PassphraseMixin,
):
    username = 'demo'
    password = 'demo'

    @property
    def element(self):
        return ElementHelper(self.browser)

    def setUp(self):
        super().setUp()
        self._setup_user()
        self._create_report()

    def _setup_user(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )
        cookie = self.client.cookies['sessionid']
        self.browser.get(self.live_server_url)
        # ref: https://github.com/ariya/phantomjs/issues/14228
        try:
            self.browser.add_cookie({
                'name': 'sessionid',
                'value': cookie.value,
                'secure': False,
                'path': '/',
            })
        except BaseException:
            self.browser.add_cookie({
                'name': 'sessionid',
                'value': cookie.value,
                'secure': False,
                'path': '/',
                'domain': 'localhost',
            })
        self.browser.get(self.live_server_url)

    def _create_report(self):
        self.element.enter_key()
        self.element.enter_key_confirmation()
        self.element.submit()


class EncryptedFrontendTest(
    FrontendTestCase,
):
    pass
