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

    def test_data_textbox(self):
        form = self.manager.get_forms()[1]
        zipped_data = self.data_manager.get_zipped_data(
            data={'question_2': 'owlette ipsum cattree'},
            forms=[form.serialized],
        )
        self.assertIn(
            [{'do androids dream of electric sheep?':
                ['owlette ipsum cattree'],
              }],
            zipped_data,
        )

    def test_data_multiple_choice(self):
        form = self.manager.get_forms()[0]
        zipped_data = self.data_manager.get_zipped_data(
            data={'question_1': ['3']},
            forms=[form.serialized],
        )
        self.assertIn(
            [{'food options': ['sugar']}],
            zipped_data,
        )

    def test_data_multiple_choice_extra_info(self):
        form = self.manager.get_forms()[0]
        zipped_data = self.data_manager.get_zipped_data(
            data={
                'question_1': ['1'],
            },
            forms=[form.serialized],
        )
        self.assertIn(
            [{'food options': ['sugar']}],
            zipped_data,
        )
