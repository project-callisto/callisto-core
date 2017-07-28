from wizard_builder.models import (
    Choice, QuestionPage, RadioButton, SingleLineText,
)

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model

from callisto_core.delivery.views import ReportDetail
from callisto_core.delivery.models import Report

User = get_user_model()


class ReviewPageTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.site = Site.objects.get(id=1)
        Site.objects.filter(id=1).update(domain='testserver')
        cls.user = User.objects.create_user(username='test', password='test')
        cls.page_1 = QuestionPage.objects.create()
        cls.page_1.sites.add(cls.site.id)
        cls.page_2 = QuestionPage.objects.create()
        cls.page_2.sites.add(cls.site.id)
        cls.question_1 = SingleLineText.objects.create(
            text='1st question',
            page=cls.page_1,
        )
        cls.question_2 = SingleLineText.objects.create(
            text='2nd question',
            page=cls.page_2,
        )

    @classmethod
    def setup_report(cls, report):
        report_text = [
            {
                'answer': '1st answer',
                'id': cls.question_1.pk,
                'question_text': cls.question_1.text,
                'type': SingleLineText._meta.verbose_name,
            },
            {
                'answer': '2nd answer',
                'id': cls.question_2.pk,
                'question_text': cls.question_2.text,
                'type': SingleLineText._meta.verbose_name,
            },
        ]
        report.encrypt_report(str(report_text), '')

    def setUp(self):
        self.client.login(username='test', password='test')
        self.report, _ = Report.objects.get_or_create(
            owner=self.user,
        )

    @property
    def template(self):
        view = ReportDetail()
        view.object = self.report
        return view.get_template_names()[0]

    @property
    def page_response(self):
        return self.client.get(
            reverse('report_details', kwargs={'uuid':self.report.uuid}),
        )

    def test_report_details_url_and_template(self):
        self.assertTemplateUsed(self.page_response, self.template)

    def test_questions_displayed_on_page(self):
        response = self.page_response
        self.assertIn('1st question', str(response.content))
        self.assertIn('2nd question', str(response.content))

    def test_answers_displayed_on_page(self):
        response = self.page_response
        self.assertIn('1st answer', str(response.content))
        self.assertIn('2nd answer', str(response.content))
