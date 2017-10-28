from django.test import TestCase

from .. import managers


class FormSerializationTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]
    expected_data = [{
        'descriptive_text': 'answer wisely',
        'field_id': 'question_2',
        'formquestion_ptr': 2,
        'id': 2,
        'page': 2,
        'position': 0,
        'question_text': 'do androids dream of electric sheep?',
        'text': 'do androids dream of electric sheep?',
        'type': 'Singlelinetext',
    }]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        form = cls.manager.get_form_models()[1]
        cls.actual_data = form.serialized

    def test_same_size(self):
        self.assertEqual(
            len(self.actual_data),
            len(self.expected_data),
        )

    def test_same_questions(self):
        for index, question in enumerate(self.expected_data):
            self.assertEqual(
                self.actual_data[index],
                question,
            )
