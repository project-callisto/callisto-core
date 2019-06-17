from unittest import skip
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from callisto_core.delivery import forms

from .. import test_base

User = get_user_model()


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ReportCreateFormTest(TestCase):

    def test_nonmatching_keys_rejected(self):
        form = forms.ReportCreateForm({
            'key': 'this is a key',
            'key_confirmation': 'this is also a key',
        }, view=MagicMock())
        self.assertFalse(form.is_valid())

    def test_matching_keys_accepted(self):
        form = forms.ReportCreateForm({
            'key': 'this is my good secret key',
            'key_confirmation': 'this is my good secret key',
        }, view=MagicMock())
        self.assertTrue(form.is_valid())


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ReportAccessFormTest(test_base.ReportFlowHelper):

    def test_wrong_key_rejected(self):
        self.client_post_report_creation()
        form = forms.ReportAccessForm(
            data={'key': 'not my key'},
            instance=self.report,
            view=MagicMock(),
        )
        form.full_clean()
        self.assertFalse(form.is_valid())

    def test_right_key_accepted(self):
        self.client_post_report_creation()
        form = forms.ReportAccessForm(
            data={'key': self.passphrase},
            instance=self.report,
            view=MagicMock(),
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
