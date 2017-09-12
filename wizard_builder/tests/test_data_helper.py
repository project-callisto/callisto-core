from django.test import TestCase

from .. import forms, managers, view_helpers


class DataHelperTest(TestCase):
    data_manager = view_helpers.SerializedDataHelper
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]

    def test_data_generates(self):
        form = self.manager.get_forms()[1]
        zipped_data = self.data_manager.get_zipped_data(
            data={'question_2': 'owlette ipsum cattree'},
            forms=[form.serialized],
        )
        self.assertIsInstance(zipped_data, list)

    def test_data_text_field(self):
        form = self.manager.get_forms()[1]
        zipped_data = self.data_manager.get_zipped_data(
            data={'question_2': 'owlette ipsum cattree'},
            forms=[form.serialized],
        )
        self.assertEqual(
            zipped_data,
            [{'do androids dream of electric sheep?': ['owlette ipsum cattree']}],
        )
