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
        expected_data = {}
        from pprint import pprint
        pprint(data)
        self.assertEqual(data, expected_data)
