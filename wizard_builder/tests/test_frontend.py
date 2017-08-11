from django.test import override_settings

from .base import FunctionalTest


class ElementHelper(object):

    def __init__(self, browser):
        self.browser = browser

    @property
    def next(self):
        return self.browser.find_element_by_css_selector(
            '[value="Next"]')

    @property
    def back(self):
        return self.browser.find_element_by_css_selector(
            '[value="Back"]')

    @property
    def extra_input(self):
        return self.browser.find_element_by_css_selector(
            '.extra-widget-text input')

    @property
    def extra_dropdown(self):
        return self.browser.find_element_by_css_selector(
            '.extra-widget-dropdown input')

    @property
    def text_input(self):
        return self.browser.find_element_by_css_selector(
            '[type="text"]')


@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    @property
    def element(self):
        return ElementHelper(self.browser)

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
        self.element.extra_dropdown.click()
        self.assertSelectorContains('option', 'option 1')
        self.assertSelectorContains('option', 'option 2')

    def test_can_navigate_to_second_page(self):
        self.element.next.click()
        self.assertSelectorContains('body', 'the second page')

    def test_can_navigate_forwards_and_back(self):
        self.element.next.click()
        self.element.back.click()
        self.assertSelectorContains('body', 'the first page')

    def test_can_select_choice(self):
        self.assertFalse(self.element.extra_input.is_selected())
        self.element.extra_input.click()
        self.assertTrue(self.element.extra_input.is_selected())

    def test_choice_1_persists_after_changing_page(self):
        self.element.extra_input.click()
        self.element.next.click()
        self.element.back.click()
        self.assertTrue(self.element.extra_input.is_selected())

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

    def test_text_persists_after_changing_page(self):
        self.element.next.click()
        self.element.text_input.send_keys('text input content!!!')
        self.element.back.click()
        self.element.next.click()
        self.assertEqual(
            'text input content!!!',
            self.element.text_input.get_attribute('value'),
        )
