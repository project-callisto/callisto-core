from django.test import TestCase

from .. import forms, managers, models


class ManagerTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]

    def _change_form_text(self, form):
        question = models.FormQuestion.objects.filter(pk=form['id'])
        question.update(text='text should be persistent')

    def _serialize(self, forms):
        return [
            form.serialized
            for form in forms
        ]

    def test_accurate_number_of_forms_present(self):
        self.assertEqual(
            len(self.manager.get_form_models()),
            len(models.Page.objects.wizard_set(1)),
        )

    def test_returns_page_form(self):
        for form in self.manager.get_form_models():
            self.assertIsInstance(form, forms.PageForm)

    def test_manager_populates_default_data(self):
        text = 'kitten ipsum cottoncloud'
        data = {'question_2': text}
        form = self.manager.get_form_models(answer_data=data)[1]
        self.assertEqual(form.cleaned_data, data)

    def test_manager_persists_form_data(self):
        form_data_before = self.manager.get_serialized_forms()
        self._change_form_text(form_data_before[0][0])
        form_data_after = self._serialize(self.manager.get_form_models(
            form_data=form_data_before))
        self.assertNotEqual(
            'text should be persistent',
            form_data_after[0][0]['question_text'],
        )
        self.assertEqual(form_data_before, form_data_after)
