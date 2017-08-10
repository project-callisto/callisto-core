import json

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.test import TestCase

from ..forms import PageForm
from ..models import Checkbox, Choice, Page, RadioButton, SingleLineText
from ..views import WizardView
from .test_app.models import Report

User = get_user_model()


def sort_json(text):
    return sorted(json.loads(text), key=lambda x: x['id'])


def get_body(response):
    return response.content.decode('utf-8')


class FormBaseTest(TestCase):

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        self.page1 = Page.objects.create()
        self.page1.sites.add(self.site.id)
        self.page2 = Page.objects.create()
        self.page2.sites.add(self.site.id)
        self.question1 = SingleLineText.objects.create(
            text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(
            text="2nd question", page=self.page2)

    def _get_wizard_response(self, wizard, form_list, **kwargs):
        # simulate what wizard does on final form submit
        wizard.processed_answers = wizard.process_answers(
            form_list=form_list, form_dict=dict(enumerate(form_list)))
        return get_body(
            wizard.done(
                form_list=form_list,
                form_dict=dict(
                    enumerate(form_list)),
                **kwargs))


class WizardIntegratedTest(FormBaseTest):

    def setUp(self):
        super(WizardIntegratedTest, self).setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

    form_url = '/wizard/new/0/'
    report_key = 'solidasarock1234rock'

    def _answer_page_one(self):
        return self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

    def _answer_page_two(self, response):
        return self.client.post(
            response.redirect_chain[0][0],
            data={
                '1-question_%i' %
                self.question2.pk: 'another answer to a different question',
                'wizard_goto_step': 2,
                'form_wizard-current_step': 1},
            follow=True)

    def test_form_displayed_on_first_page(self):
        response = self.client.get(self.form_url)
        self.assertIsInstance(response.context['form'], PageForm)
