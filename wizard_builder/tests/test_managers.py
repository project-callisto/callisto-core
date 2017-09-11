from django.test import TestCase

from .. import forms, managers, models


class ManagerTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]

    def test_accurate_number_of_forms_present(self):
        self.assertEqual(
            len(self.manager.get_forms({}, 1)),
            len(models.Page.objects.wizard_set(1)),
        )

    def test_returns_page_form(self):
        for form in self.manager.get_forms({}, 1):
            self.assertIsInstance(form, forms.PageForm)
