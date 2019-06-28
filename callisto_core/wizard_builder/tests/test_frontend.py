from unittest import skip

from selenium.webdriver.support.ui import Select

from django.test import override_settings

from callisto_core.wizard_builder import models, view_helpers


class ElementHelper(object):
    def __init__(self, browser):
        self.browser = browser

    @property
    def done(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.review_name)
        )

    @property
    def next(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.next_name)
        )

    @property
    def back(self):
        return self.browser.find_element_by_css_selector(
            '[value="{}"]'.format(view_helpers.StepsHelper.back_name)
        )

    @property
    def extra_input(self):
        return self.browser.find_element_by_css_selector("#id_question_1_0")

    @property
    def extra_dropdown(self):
        return self.browser.find_element_by_css_selector("#id_question_1_1")

    @property
    def dropdown_select(self):
        return self.browser.find_element_by_css_selector("select.extra-widget-dropdown")

    @property
    def choice_1(self):
        return self.choice_number(0)

    @property
    def choice_3(self):
        return self.choice_number(2)

    @property
    def text_input(self):
        return self.browser.find_element_by_css_selector('[type="text"]')

    def wait_for_display(self):
        # / really unreliable way to wait for the element to be displayed
        self.next.click()
        self.back.click()

    def choice_number(self, number):
        return self.browser.find_elements_by_css_selector('[type="checkbox"]')[number]
