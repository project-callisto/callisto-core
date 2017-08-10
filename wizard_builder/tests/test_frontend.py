from django.test import override_settings

from .base import FunctionalTest


@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    def test_first_page_text(self):
        self.assertSelectorContains('body', 'the first page')

    def test_submit_presence(self):
        self.assertCss('[type="submit"]')

    def test_step_0_presence(self):
        self.assertCss('[name="wizard_current_step"]')
        self.assertCss('[value="0"]')

    def test_question_fields(self):
        self.assertSelectorContains('h2', 'main text')
        self.assertSelectorContains('.help-block', 'descriptive text')

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
            '[value="Next"]').click()
        self.assertSelectorContains('body', 'the second page')

    def test_can_navigate_forwards_and_back(self):
        self.browser.find_element_by_css_selector(
            '[value="Next"]').click()
        self.browser.find_element_by_css_selector(
            '[value="Back"]').click()
        self.assertSelectorContains('body', 'the first page')
