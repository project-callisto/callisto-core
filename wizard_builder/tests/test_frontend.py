from unittest import skip

from django.test import override_settings

from .. import models, view_helpers
from .base import FunctionalTest


class Model(object):

    @property
    def page_1(self):
        return models.Page.objects.all()[0]

    @property
    def page_2(self):
        return models.Page.objects.all()[1]

    @property
    def page_3(self):
        return models.Page.objects.all()[2]

    @property
    def page_1_question_1(self):
        return self.page_1.questions[0]

    @property
    def page_1_question_2(self):
        return self.page_1.questions[1]

    @property
    def page_1_question_1_choice_1(self):
        return self.page_1_question_1.choices[0]

    @property
    def page_1_question_1_choice_2(self):
        return self.page_1_question_1.choices[1]

    @property
    def page_1_question_1_choice_3(self):
        return self.page_1_question_1.choices[2]

    @property
    def dropdown_1(self):
        return self.page_1_question_1_choice_2.options[0]

    @property
    def dropdown_2(self):
        return self.page_1_question_1_choice_2.options[1]


model = Model()


class ElementHelper(object):

    def __init__(self, browser):
        self.browser = browser

    @property
    def done(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.review_name))

    @property
    def next(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.next_name))

    @property
    def back(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.back_name))

    @property
    def extra_input(self):
        return self.browser.find_element_by_css_selector(
            '.extra-widget-text input')

    @property
    def extra_dropdown(self):
        return self.browser.find_element_by_css_selector(
            '.extra-widget-dropdown input')

    @property
    def choice_1(self):
        return self.choice_number(0)

    @property
    def choice_3(self):
        return self.choice_number(2)

    @property
    def text_input(self):
        return self.browser.find_element_by_css_selector(
            '[type="text"]')

    def choice_number(self, number):
        return self.browser.find_elements_by_css_selector(
            '[type="checkbox"]')[number]


@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    # TODO: review screen tests

    @property
    def element(self):
        return ElementHelper(self.browser)

    def test_first_page_text(self):
        self.assertSelectorContains('form', model.page_1.infobox)

    def test_second_page_text(self):
        self.element.next.click()
        self.assertSelectorContains('form', model.page_2.infobox)

    def test_third_page_text(self):
        self.element.next.click()
        self.element.next.click()
        self.assertSelectorContains('form', model.page_3.infobox)
        self._assert_page_contents()

    def _assert_page_contents(self):
        self.assertCss('[type="submit"]')
        self.assertCss('[name="{}"]'.format(
            view_helpers.StepsHelper.wizard_current_name,
        ))
        self.assertCss('[name="{}"]'.format(
            view_helpers.StepsHelper.wizard_goto_name,
        ))
        self.assertCss('[name="{}"]'.format(
            view_helpers.StorageHelper.form_pk_field,
        ))

    def test_forwards_and_backwards_navigation(self):
        self.element.next.click()
        self.element.back.click()
        self.assertSelectorContains('form', model.page_1.infobox)
        self.element.next.click()
        self.element.next.click()
        self.element.back.click()
        self.assertSelectorContains('form', model.page_2.infobox)

    def test_first_page_questions(self):
        self.assertSelectorContains('form', model.page_1_question_1.text)
        self.assertSelectorContains(
            'form', model.page_1_question_1.descriptive_text)
        self.assertSelectorContains('form', model.page_1_question_2.text)
        self.assertSelectorContains(
            'form', model.page_1_question_2.descriptive_text)

    def test_first_page_choices(self):
        self.assertSelectorContains(
            'form', model.page_1_question_1_choice_1.text)
        self.assertSelectorContains(
            'form', model.page_1_question_1_choice_2.text)
        self.assertSelectorContains(
            'form', model.page_1_question_1_choice_3.text)

    def test_extra_info(self):
        self.assertCss('[placeholder="extra information here"]')

    @skip('unreliable test')
    def test_extra_dropdown(self):
        self.element.extra_dropdown.click()
        self.assertSelectorContains('option', model.dropdown_1.text)
        self.assertSelectorContains('option', model.dropdown_2.text)

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
        self.assertSelectorContains(
            'body', model.page_1_question_1_choice_1.text)

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
        self.assertSelectorContains('body', model.page_1_question_1.text)
        self.assertSelectorContains('body', model.page_1_question_2.text)
