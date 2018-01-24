from django.test import TestCase

from callisto_core.wizard_builder import forms, managers, mocks


class FormSerializationTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]
    expected_data = [{
        'descriptive_text': 'answer wisely',
        'field_id': 'question_2',
        'id': 2,
        'page': 2,
        'position': 0,
        'sites': [1],
        'question_text': 'do androids dream of electric sheep?',
        'text': 'do androids dream of electric sheep?',
        'type': 'singlelinetext',
        'choices': [],
    }]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        form = cls.manager.get_form_models()[1]
        cls.actual_data = form.serialized

    def test_same_size(self):
        actual_data = self.actual_data
        expected_data = self.expected_data
        self.assertEqual(
            len(actual_data),
            len(expected_data),
        )

    def test_same_questions(self):
        actual_data = self.actual_data
        expected_data = self.expected_data
        for index, expected_question in enumerate(expected_data):
            actual_question = actual_data[index]
            self.assertEqual(
                actual_question,
                expected_question,
            )
