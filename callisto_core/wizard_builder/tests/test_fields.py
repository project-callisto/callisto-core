from django.test import TestCase

from .. import fields


class FieldOptionsTest(TestCase):
    def test_field_options_displayed(self):
        field_options = fields.get_field_options()
        for item in ["singlelinetext", "textarea", "checkbox", "radiobutton"]:
            self.assertIn((item, item), field_options)
