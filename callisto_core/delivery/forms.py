import logging

from nacl.exceptions import CryptoError

from django import forms
from django.contrib.auth import get_user_model

from . import fields, models

logger = logging.getLogger(__name__)
User = get_user_model()


def passphrase_field(label):
    return forms.CharField(
        max_length=64,
        label=label,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',
            'class': 'form-control',
        }),
    )


class FormViewExtensionMixin(object):

    def __init__(self, *args, **kwargs):
        self.view = kwargs.pop('view')  # TODO: pass in something more specific
        super().__init__(*args, **kwargs)


class ReportBaseForm(
    FormViewExtensionMixin,
    forms.models.ModelForm,
):
    key = fields.PassphraseField(label='Passphrase')

    @property
    def report(self):
        return self.instance

    class Meta:
        model = models.Report
        fields = []


class ReportCreateForm(ReportBaseForm):
    message_confirmation_error = "key and key confirmation must match"
    key_confirmation = fields.PassphraseField(label='Confirm Passphrase')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.view.request.user
        if isinstance(user, User):
            self.instance.owner = user

    def clean_key_confirmation(self):
        key = self.data.get("key")
        key_confirmation = self.data.get("key_confirmation")
        if key != key_confirmation:
            raise forms.ValidationError(self.message_confirmation_error)
        else:
            return key_confirmation


class ReportAccessForm(ReportBaseForm):
    # TODO: form.save() should add key to storage?
    message_key_error = 'Invalid passphrase'
    message_key_error_log = 'decryption failure on {}'

    def clean_key(self):
        try:
            return self._decrypt_report()
        except CryptoError:
            return self._decryption_failed()

    def _decrypt_report(self):
        self.decrypted_report = self.report.decrypted_report(
            self.data['key'])
        return self.data['key']

    def _decryption_failed(self):
        logger.info(self.message_key_error_log.format(self.report))
        raise forms.ValidationError(self.message_key_error)
