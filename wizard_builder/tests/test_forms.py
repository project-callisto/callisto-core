from django.test import TestCase

from .. import managers


class FormSerializationTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]

    def test_serialized_data_format(self):
        form = self.manager.get_form_models()[1]
        data = form.serialized
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
        self.assertEqual(data, expected_data)
