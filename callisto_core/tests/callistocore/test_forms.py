from unittest.mock import MagicMock

from callisto_core.delivery import forms

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .. import test_base

User = get_user_model()


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
            data={'key': self.secret_key},
            instance=self.report,
            view=MagicMock(),
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
