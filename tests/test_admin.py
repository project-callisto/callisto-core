from selenium import webdriver

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.sites.models import Site

from wizard_builder.models import PageBase


User = get_user_model()


@override_settings(DEBUG=True)
class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(FunctionalTest, cls).setUpClass()
        cls.browser = webdriver.Firefox()
        # cls.browser = webdriver.PhantomJS()
        cls.browser.implicitly_wait(3)
        Site.objects.update(domain='localhost')

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(FunctionalTest, cls).tearDownClass()

    def setUp(self):
        super(FunctionalTest, self).setUp()
        User.objects.create_superuser('user', '', 'pass')
        self.login_admin()

    def login_admin(self):
        self.browser.get(self.live_server_url + '/admin/login/')
        self.browser.find_element_by_id('id_username').clear()
        self.browser.find_element_by_id('id_username').send_keys('user')
        self.browser.find_element_by_id('id_password').clear()
        self.browser.find_element_by_id('id_password').send_keys('pass')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()

    def test_can_load_admin_with_wizard_builder_on_it(self):
        self.assertTrue('Django administration' in self.browser.page_source)
        self.assertTrue('Wizard Builder' in self.browser.page_source)
