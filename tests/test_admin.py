from selenium import webdriver

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

User = get_user_model()


@override_settings(DEBUG=True)
class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(FunctionalTest, cls).setUpClass()
        # cls.browser = webdriver.Firefox()
        cls.browser = webdriver.PhantomJS()
        cls.browser.implicitly_wait(3)
        # not in setUpTestData because they need to happen before login
        Site.objects.update(domain='localhost')
        User.objects.create_superuser('user', '', 'pass')
        cls.login_admin()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(FunctionalTest, cls).tearDownClass()

    @classmethod
    def login_admin(cls):
        cls.browser.get(cls.live_server_url + '/admin/login/')
        cls.browser.find_element_by_id('id_username').clear()
        cls.browser.find_element_by_id('id_username').send_keys('user')
        cls.browser.find_element_by_id('id_password').clear()
        cls.browser.find_element_by_id('id_password').send_keys('pass')
        cls.browser.find_element_by_css_selector('input[type="submit"]').click()

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        super(FunctionalTest, self).setUp()
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
