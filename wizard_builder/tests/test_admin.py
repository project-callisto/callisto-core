import os
from datetime import datetime
from distutils.util import strtobool

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from ..models import (
    Checkbox, Choice, Date, FormQuestion, MultiLineText, MultipleChoice, Page,
    RadioButton, SingleLineText, SingleLineTextWithMap,
)

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


User = get_user_model()

SCREEN_DUMP_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'screendumps'
)


class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.quit()
        except (AttributeError, OSError):
            pass  # brower has already been quit!
        super(FunctionalTest, cls).tearDownClass()

    @classmethod
    def setUpClass(cls):
        super(FunctionalTest, cls).setUpClass()
        if strtobool(os.environ.get('WEBDRIVER_FIREFOX', 'False').lower()):
            # swap on with:
            #   export WEBDRIVER_FIREFOX='True'
            cls.browser = webdriver.Firefox()
        else:
            cls.browser = webdriver.PhantomJS()

    def tearDown(self):
        if self._test_has_failed():
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)
            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid = ix
                self.browser.switch_to.window(handle)
                self.take_screenshot()
                self.dump_html()
        super(FunctionalTest, self).tearDown()

    def wait_for_until_body_loaded(self):
        WebDriverWait(self.browser, 3).until(
            lambda driver: driver.find_element_by_tag_name('body'),
        )

    def _test_has_failed(self):
        try:
            for method, error in self._outcome.errors:
                if error:
                    return True
        except AttributeError:
            pass  # not all python versions has access to self._outcome
        return False

    def take_screenshot(self):
        filename = self._get_filename() + '.png'
        print('screenshotting to', filename)
        self.browser.get_screenshot_as_file(filename)

    def dump_html(self):
        filename = self._get_filename() + '.html'
        print('dumping page HTML to', filename)
        with open(filename, 'w') as f:
            f.write(self.browser.page_source)

    def _get_filename(self):
        timestamp = datetime.now().isoformat().replace(':', '.')[:19]
        return '{folder}/{classname}.{method}-window{windowid}-{timestamp}'.format(
            folder=SCREEN_DUMP_LOCATION,
            classname=self.__class__.__name__,
            method=self._testMethodName,
            windowid=self._windowid,
            timestamp=timestamp
        )


@override_settings(DEBUG=True)
class AdminFunctionalTest(FunctionalTest):

    def login_admin(self):
        self.browser.get(self.live_server_url + '/admin/login/')
        self.browser.find_element_by_id('id_username').clear()
        self.browser.find_element_by_id('id_username').send_keys('user')
        self.browser.find_element_by_id('id_password').clear()
        self.browser.find_element_by_id('id_password').send_keys('pass')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        port = urlparse(cls.live_server_url).port
        Site.objects.create(domain='localhost')
        Site.objects.create(domain='localhost:{}'.format(port))
        User.objects.create_superuser('user', '', 'pass')

    def setUp(self):
        super().setUp()
        self.login_admin()
        self.browser.get(self.live_server_url + '/admin/')
        self.wait_for_until_body_loaded()

    def test_can_load_admin_with_wizard_builder_on_it(self):
        self.assertIn('Django administration', self.browser.page_source)
        self.assertIn('Wizard Builder', self.browser.page_source)

    def test_can_see_all_models(self):
        wizard_builder_models = [
            Page,
            FormQuestion,
            SingleLineText,
            SingleLineTextWithMap,
            MultiLineText,
            MultipleChoice,
            Checkbox,
            RadioButton,
            Choice,
            Date,
        ]
        for Model in wizard_builder_models:
            self.assertIn(Model._meta.verbose_name.lower(), self.browser.page_source.lower())
