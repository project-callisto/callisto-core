from django.test import override_settings

from .base import FunctionalTest


@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    def test_submit_presence(self):
        self.assertCss('[type="submit"]')

    def test_step_0_presence(self):
        self.assertCss('[name="current_step"]')
        self.assertCss('[value="0"]')

    def test_question_fields(self):
        self.assertSelectorContains('h2', 'text!!!')
        self.assertSelectorContains('.help-block', '~descriptive text~')

    def test_choice_text(self):
        self.assertSelectorContains('li', 'choice 1')
        self.assertSelectorContains('li', 'choice 2')

    def test_extra_info(self):
        self.assertCss('[placeholder="extra information here"]')

    def test_extra_dropdown(self):
        self.browser.find_element_by_css_selector(
            '.extra_options input').click()
        self.assertSelectorContains('option', 'option 1')
        self.assertSelectorContains('option', 'option 2')

    def test_can_navigate_to_second_page(self):
        self.browser.find_element_by_css_selector(
            '[type="submit"]').click()
        self.assertSelectorContains('body', 'the second page')
