from django.test import override_settings

from .base import FunctionalTest


@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    @property
    def _next(self):
        return self.browser.find_element_by_css_selector(
            '[value="Next"]')

    @property
    def _back(self):
        return self.browser.find_element_by_css_selector(
            '[value="Back"]')

    @property
    def _extra_input(self):
        return self.browser.find_element_by_css_selector(
            '.extra_options input')

    def test_first_page_text(self):
        self.assertSelectorContains('body', 'the first page')

    def test_submit_presence(self):
        self.assertCss('[type="submit"]')

    def test_wizard_attrs_presence(self):
        self.assertCss('[name="wizard_current_step"]')
        self.assertCss('[name="wizard_goto_step"]')
        self.assertCss('[name="form_pk"]')

    def test_question_fields(self):
        self.assertSelectorContains('h2', 'main text')
        self.assertSelectorContains('.help-block', 'descriptive text')

    def test_choice_text(self):
        self.assertSelectorContains('li', 'choice 1')
        self.assertSelectorContains('li', 'choice 2')

    def test_extra_info(self):
        self.assertCss('[placeholder="extra information here"]')

    def test_extra_dropdown(self):
        self._extra_input.click()
        self.assertSelectorContains('option', 'option 1')
        self.assertSelectorContains('option', 'option 2')

    def test_can_navigate_to_second_page(self):
        self._next.click()
        self.assertSelectorContains('body', 'the second page')

    def test_can_navigate_forwards_and_back(self):
        self._next.click()
        self._back.click()
        self.assertSelectorContains('body', 'the first page')

    def test_choices_persist_after_forwards_and_back(self):
        self.assertFalse(self._extra_input.is_selected())
        self._extra_input.click()
        self.assertTrue(self._extra_input.is_selected())

        self._next.click()
        self._back.click()

        self.assertTrue(self._extra_input.is_selected())
        self.assertSelectorContains('body', 'the first page')
