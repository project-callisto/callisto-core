import logging
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.test import override_settings

from ..models import (
    Checkbox, Choice, Date, FormQuestion, MultiLineText, MultipleChoice, Page,
    RadioButton, SingleLineText, SingleLineTextWithMap,
)
from .base import FunctionalTest


User = get_user_model()


@override_settings(DEBUG=True)
class AdminFunctionalTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        User.objects.create_superuser('user', '', 'pass')
        self.login_admin()
        self.browser.get(self.live_server_url + '/admin/')
        self.wait_for_until_body_loaded()

    def login_admin(self):
        self.browser.get(self.live_server_url + '/admin/login/')
        self.browser.find_element_by_id('id_username').clear()
        self.browser.find_element_by_id('id_username').send_keys('user')
        self.browser.find_element_by_id('id_password').clear()
        self.browser.find_element_by_id('id_password').send_keys('pass')
        self.browser.find_element_by_css_selector('input[type="submit"]').click()

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
