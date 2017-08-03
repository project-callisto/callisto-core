import os
from datetime import datetime
from distutils.util import strtobool
from unittest import skip

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from ..models import (
    Checkbox, Choice, Date, FormQuestion, MultiLineText, MultipleChoice,
    QuestionPage, RadioButton, SingleLineText, SingleLineTextWithMap,
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
            QuestionPage,
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

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_question_page_question_inline_present(self):
        self.browser.find_element_by_link_text(QuestionPage._meta.verbose_name.capitalize() + 's').click()
        self.browser.find_element_by_css_selector('.addlink').click()
        self.assertIn(FormQuestion._meta.verbose_name_plural.capitalize(), self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_question_page_local_fields_present(self):
        self.browser.find_element_by_link_text(QuestionPage._meta.verbose_name.capitalize() + 's').click()
        self.browser.find_element_by_css_selector('.addlink').click()
        self.assertIn('id_infobox', self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_can_add_question_page(self):
        self.browser.find_element_by_link_text(QuestionPage._meta.verbose_name.capitalize() + 's').click()
        self.assertNotIn('1337', self.browser.page_source)
        self.browser.find_element_by_css_selector('.addlink').click()
        self.browser.find_element_by_css_selector('#id_position').send_keys('1337')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        self.assertIn('1337', self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_can_edit_question_page(self):
        QuestionPage.objects.create()
        self.browser.find_element_by_link_text(QuestionPage._meta.verbose_name.capitalize() + 's').click()
        self.assertNotIn('1337', self.browser.page_source)
        self.browser.find_element_by_css_selector('.addlink').click()
        self.browser.find_element_by_css_selector('#id_position').send_keys('1337')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        self.assertIn('1337', self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_form_question_models_downcast(self):
        QuestionPage.objects.create()
        form_question_models = [
            SingleLineText,
            SingleLineTextWithMap,
            MultiLineText,
            MultipleChoice,
            Checkbox,
            RadioButton,
        ]
        for Model in form_question_models:
            Model.objects.create()
        self.browser.find_element_by_link_text(FormQuestion._meta.verbose_name.capitalize() + 's').click()
        for Model in form_question_models:
            self.assertIn(Model._meta.verbose_name.capitalize(), self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_multiple_choice_models_downcast(self):
        QuestionPage.objects.create()
        Checkbox.objects.create()
        RadioButton.objects.create()
        self.browser.find_element_by_link_text(MultipleChoice._meta.verbose_name.capitalize() + 's').click()
        self.assertIn(MultipleChoice._meta.verbose_name_plural.capitalize(), self.browser.page_source)
        self.assertIn(Checkbox._meta.verbose_name.capitalize(), self.browser.page_source)
        self.assertIn(RadioButton._meta.verbose_name.capitalize(), self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_can_access_radio_button_from_form_question(self):
        QuestionPage.objects.create()
        RadioButton.objects.create()
        self.browser.find_element_by_link_text(FormQuestion._meta.verbose_name.capitalize() + 's').click()
        self.browser.find_element_by_link_text(RadioButton._meta.verbose_name.capitalize()).click()
        self.assertIn(RadioButton._meta.verbose_name_plural.capitalize(), self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_radio_button_choices_present(self):
        self.browser.find_element_by_link_text(RadioButton._meta.verbose_name.capitalize() + 's').click()
        self.browser.find_element_by_css_selector('.addlink').click()
        self.assertIn(Choice._meta.verbose_name_plural.capitalize(), self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_can_add_radio_button(self):
        QuestionPage.objects.create()
        self.browser.find_element_by_link_text(RadioButton._meta.verbose_name.capitalize() + 's').click()
        self.assertNotIn('unique_cattens', self.browser.page_source)
        self.browser.find_element_by_css_selector('.addlink').click()
        self.browser.find_element_by_css_selector('#id_text').send_keys('unique_cattens')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        self.assertIn('unique_cattens', self.browser.page_source)

    @skip('https://github.com/SexualHealthInnovations/django-wizard-builder/issues/45')
    def test_can_edit_radio_button(self):
        QuestionPage.objects.create()
        RadioButton.objects.create()
        self.browser.find_element_by_link_text(RadioButton._meta.verbose_name.capitalize() + 's').click()
        self.assertNotIn('unique_cattens', self.browser.page_source)
        self.browser.find_element_by_css_selector('.addlink').click()
        self.browser.find_element_by_css_selector('#id_text').send_keys('unique_cattens')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        self.assertIn('unique_cattens', self.browser.page_source)
