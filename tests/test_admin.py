import os
from datetime import datetime

from selenium import webdriver

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

User = get_user_model()

SCREEN_DUMP_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'screendumps'
)


class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(FunctionalTest, cls).setUpClass()
        # TODO: an env switch for this
        # cls.browser = webdriver.Firefox()
        cls.browser = webdriver.PhantomJS()
        cls.browser.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(FunctionalTest, cls).tearDownClass()

    def tearDown(self):
        if self._test_has_failed():
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)
            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid = ix
                self.browser.switch_to.window(handle)
                self.take_screenshot()
                self.dump_html()
        self.browser.quit()
        super().tearDown()

    def _test_has_failed(self):
        for method, error in self._outcome.errors:
            if error:
                return True
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

    def setUp(self):
        super(FunctionalTest, self).setUp()
        Site.objects.update(domain='localhost')
        User.objects.create_superuser('user', '', 'pass')
        self.login_admin()
        self.browser.get(self.live_server_url + '/admin/')

    def test_can_load_admin_with_wizard_builder_on_it(self):
        self.assertTrue('Django administration' in self.browser.page_source)
        self.assertTrue('Wizard Builder' in self.browser.page_source)

    def test_can_see_all_models(self):
        pass

    def test_pagebase_models_downcast(self):
        pass

    def test_can_access_question_page_through_page_base(self):
        pass

    def test_question_page_question_inline_present(self):
        pass

    def test_question_page_local_fields_present(self):
        pass

    def test_can_add_question_page(self):
        pass

    def test_can_edit_question_page(self):
        pass

    def test_form_question_models_downcast(self):
        pass

    def test_multiple_choice_models_downcast(self):
        pass

    def test_can_access_radio_button_from_form_question(self):
        pass

    def test_radio_button_choices_present(self):
        pass

    def test_can_add_radio_button(self):
        pass

    def test_can_edit_radio_button(self):
        pass
