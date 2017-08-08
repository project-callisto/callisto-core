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
        self.assertSelectorContains('.choice', 'choice 1')
        self.assertSelectorContains('.choice', 'choice 2')

    def test_extra_options(self):
        self.assertSelectorContains('option', 'option 1')
        self.assertSelectorContains('option', 'option 2')
