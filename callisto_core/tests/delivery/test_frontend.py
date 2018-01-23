import logging
import os
import time
import unittest
from datetime import datetime
from distutils.util import strtobool
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from callisto_core.delivery.models import Report
from callisto_core.wizard_builder.models import Choice
from callisto_core.wizard_builder.tests import (
    test_frontend as wizard_builder_tests,
)

logger = logging.getLogger(__name__)

User = get_user_model()
SCREEN_DUMP_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'screendumps'
)


def headless_mode():
    return not strtobool(os.environ.get('HEADED', 'False'))


class AuthMixin:
    passphrase = 'soooooo seekrit'
    username = 'demo'
    password = 'demodemodemo123123'


class AssertionsMixin(object):

    def assertCss(self, css):
        self.assertTrue(
            self.browser.find_elements_by_css_selector(css),
        )

    def _getElements(self, css, text):
        elements = list(self.browser.find_elements_by_css_selector(css)),
        elements = elements[0]
        element_text = ''
        for element in elements:
            element_text += element.text
        return element_text

    def _selectorContains(self, text, element_text):
        assertion_valid = False
        if text in element_text:
            assertion_valid = True
        return assertion_valid

    def assertSelectorContains(self, css, text):
        element_text = self._getElements(css, text)
        if not self._selectorContains(text, element_text):
            raise AssertionError('''
                '{}' not found in '{}'
            '''.format(text, element_text))

    def assertSelectorNotContains(self, css, text):
        element_text = self._getElements(css, text)
        if self._selectorContains(text, element_text):
            raise AssertionError('''
                '{}' found in '{}'
            '''.format(text, element_text))


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


@override_settings(DEBUG=True)
class EncryptedFrontendTest(
    AuthMixin,
    AssertionsMixin,
    StaticLiveServerTestCase,
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
        # deactivate with `HEADED=TRUE pytest...`
        if headless_mode():
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

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.quit()
        except (AttributeError, OSError):
            pass  # brower has already been quit!
        super().tearDownClass()

    def wait_for_until_body_loaded(self):
        WebDriverWait(self.browser, 3).until(
            lambda driver: driver.find_element_by_tag_name('body'),
        )

    def setup_user(self):
        User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        self.browser.get(self.live_server_url)
        self.element.enter_username()
        self.browser.find_element_by_css_selector(
            '[name="password1"]').send_keys(self.password)
        self.browser.find_element_by_css_selector(
            '[name="password2"]').send_keys(self.password)
        self.browser.find_element_by_css_selector(
            '[name="terms"]').click()
        self.element.submit()

    def setup_report(self):
        self.browser.get(self.live_server_url + reverse('report_new'))
        self.element.enter_key()
        self.element.enter_key_confirmation()
        self.element.submit()
        self.report = Report.objects.first()

    def setUp(self):
        super().setUp()

        port = urlparse(self.live_server_url).port
        Site.objects.filter(id=1).update(domain='localhost:{}'.format(port))
        self.browser.get(self.live_server_url)
        self.wait_for_until_body_loaded()

        self.setup_user()
        self.setup_report()
        url = reverse(
            'report_update',
            kwargs={'uuid': self.report.uuid, 'step': 0}
        )
        self.browser.get(self.live_server_url + url)

    def tearDown(self):
        if self._test_has_failed():
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)
            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid = ix
                self.browser.switch_to.window(handle)
                self._take_screenshot()
                self._dump_html()
        super().tearDown()

    def _test_has_failed(self):
        try:
            for method, error in self._outcome.errors:
                if error:
                    return True
        except AttributeError:
            pass  # not all python versions has access to self._outcome
        return False

    def _take_screenshot(self):
        filename = self._get_filename() + '.png'
        logger.info('screenshotting to {}'.format(filename))
        self.browser.get_screenshot_as_file(filename)

    def _dump_html(self):
        filename = self._get_filename() + '.html'
        logger.info('dumping page HTML to {}'.format(filename))
        with open(filename, 'w') as f:
            f.write(self.browser.page_source)

    def _get_filename(self):
        timestamp = datetime.now().isoformat().replace(':', '.')[:19]
        return '{folder}/{classname}.{method}-window{windowid}-{timestamp}'.format(
            folder=SCREEN_DUMP_LOCATION,
            classname=self.__class__.__name__,
            method=self._testMethodName,
            windowid=self._windowid,
            timestamp=timestamp)


class ExtraInfoNameClashCases(
    EncryptedFrontendTest,
):

    def setUp(self):
        # add a second extra info question on the 1st page
        Choice.objects.filter(text='sugar').update(
            extra_info_text='what type???')
        super().setUp()

        self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="checkbox"]')[0].click()
        self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="checkbox"]')[1].click()
        self.element.wait_for_display()

        self.text_input_one = 'brown cinnamon'
        self.text_input_two = 'white diamond'
        self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="text"]')[0].send_keys(self.text_input_one)
        self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="text"]')[1].send_keys(self.text_input_two)

    def test_input_one_persists(self):
        self.element.next.click()
        self.element.back.click()
        element = self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="text"]')[0]
        self.assertEqual(
            element.get_attribute('value'),
            self.text_input_one,
        )

    def test_input_two_persists(self):
        self.element.next.click()
        self.element.back.click()
        element = self.browser.find_elements_by_css_selector(
            '.extra-widget-text [type="text"]')[1]
        self.assertEqual(
            element.get_attribute('value'),
            self.text_input_two,
        )

    def test_review_page_has_input_one(self):
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', self.text_input_one)

    def test_review_page_has_input_two(self):
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', self.text_input_two)


class WizardFrontendCases(
    EncryptedFrontendTest,
):

    def test_first_page_text(self):
        self.assertSelectorContains('form', 'food options')

    def test_second_page_text(self):
        self.element.next.click()
        self.assertSelectorContains(
            'form', 'do androids dream of electric sheep?')

    def test_third_page_text(self):
        self.element.next.click()
        self.element.next.click()
        self.assertSelectorContains('form', 'whats on the radios?')

    def test_forwards_and_backwards_navigation(self):
        self.element.next.click()
        self.element.back.click()
        self.assertSelectorContains('form', 'food options')
        self.element.next.click()
        self.element.next.click()
        self.element.back.click()
        self.assertSelectorContains(
            'form', 'do androids dream of electric sheep?')

    def test_first_page_questions(self):
        self.assertSelectorContains('form', 'food options')
        self.assertSelectorContains('form', 'choose some!')
        self.assertSelectorContains('form', 'eat it now???')
        self.assertSelectorContains('form', '')

    def test_first_page_choices(self):
        self.assertSelectorContains('form', 'vegetables')
        self.assertSelectorContains('form', 'apples')
        self.assertSelectorContains('form', 'sugar')

    def test_extra_info(self):
        self.assertCss('[placeholder="extra information here"]')

    def test_extra_dropdown(self):
        self.element.extra_dropdown.click()
        self.element.wait_for_display()
        self.assertSelectorContains('option', 'green')
        self.assertSelectorContains('option', 'red')

    def test_extra_dropdown_persists(self):
        self.element.extra_dropdown.click()
        self.element.wait_for_display()

        self.assertEqual(
            self.element.dropdown_select.get_attribute('value'),
            '1',
        )

        select = Select(self.element.dropdown_select)
        select.select_by_value('2')

        self.element.next.click()
        self.element.back.click()

        self.assertEqual(
            self.element.dropdown_select.get_attribute('value'),
            '2',
        )

    def test_can_select_choice(self):
        self.assertFalse(self.element.extra_input.is_selected())
        self.element.extra_input.click()
        self.assertTrue(self.element.extra_input.is_selected())

    def test_choice_1_persists_after_changing_page(self):
        self.element.extra_input.click()
        self.element.next.click()
        self.element.back.click()
        self.assertTrue(self.element.extra_input.is_selected())

    def test_ghost_choices_not_populated(self):
        self.element.next.click()
        self.element.back.click()
        self.assertFalse(self.element.extra_input.is_selected())
        self.assertFalse(self.element.extra_dropdown.is_selected())
        self.assertFalse(self.element.choice_3.is_selected())

    def test_choice_2_persists_after_changing_page(self):
        self.element.extra_dropdown.click()
        self.element.next.click()
        self.element.back.click()
        self.assertTrue(self.element.extra_dropdown.is_selected())

    def test_all_choices_persist_after_changing_page(self):
        self.element.extra_input.click()
        self.element.extra_dropdown.click()
        self.element.next.click()
        self.element.back.click()
        self.assertTrue(self.element.extra_input.is_selected())
        self.assertTrue(self.element.extra_dropdown.is_selected())

    def test_mulitple_answers_reflected_on_review_page(self):
        self.element.extra_input.click()
        self.element.extra_dropdown.click()
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', 'apples')
        self.assertSelectorContains('body', 'vegetables')

    def test_textbox_array_regression(self):
        self.element.next.click()
        self.element.text_input.send_keys('text input content!!!')
        self.element.back.click()
        self.element.next.click()
        self.assertNotEqual(
            ['text input content!!!'],
            self.element.text_input.get_attribute('value'),
        )

    def test_text_persists_after_changing_page(self):
        self.element.next.click()
        self.element.text_input.send_keys('text input content!!!')
        self.element.back.click()
        self.element.next.click()
        self.assertEqual(
            'text input content!!!',
            self.element.text_input.get_attribute('value'),
        )

    def test_can_render_done_page(self):
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('h2', 'Question Review')

    def test_choice_present_on_done_page(self):
        self.element.choice_1.click()
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', 'vegetables')

    def test_text_input_present_on_done_page(self):
        self.element.next.click()
        self.element.text_input.send_keys('text input content!!!')
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', 'text input content!!!')

    def test_unanswered_questions_present_on_done_page(self):
        self.element.next.click()
        self.element.next.click()
        self.element.done.click()
        self.assertSelectorContains('body', 'food options')
        self.assertSelectorContains(
            'body', 'do androids dream of electric sheep?')
        self.assertSelectorContains('body', '[ Not Answered ]')


class CallistoCoreCases(
    EncryptedFrontendTest,
):

    def test_dashboard_title(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.assertSelectorContains('h2', 'My Records')

    def test_edit_sends_you_to_first_question(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text('Edit Record').click()
        self.element.enter_key()
        self.element.submit()
        self.assertSelectorContains('form', 'food options')

    def test_can_delete_record(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text('Delete').click()
        self.element.enter_key()
        self.element.submit()
        self.assertSelectorContains('.dashboard', 'No Reports')

    def test_reporting_flow_form_redirect(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text(
            'Start reporting process').click()
        self.element.enter_key()
        self.element.submit()
        self.assertSelectorNotContains('.has-error', 'Error:')

    def test_matching_flow_form_redirect(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text(
            'Start matching process').click()
        self.element.enter_key()
        self.element.submit()
        self.assertSelectorNotContains('.has-error', 'Error:')

    def test_matching_flow_form_error(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text(
            'Start matching process').click()
        self.element.enter_key()
        self.element.submit()
        self.element.submit()
        self.assertSelectorContains('.has-error', 'Error:')

    @unittest.skipIf(headless_mode(), 'Not supported headless browsers')
    def test_can_view_pdf(self):
        self.browser.get(self.live_server_url + reverse('dashboard'))
        self.browser.find_element_by_link_text('View PDF').click()
        self.element.enter_key()
        self.element.submit()
        self.wait_for_until_body_loaded()
        self.assertIn('type="application/pdf"', self.browser.page_source)
