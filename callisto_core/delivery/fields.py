from django import forms


class PassphraseField(forms.CharField):
    widget = forms.PasswordInput(
        attrs={
            'autocomplete': 'off',
            'class': 'form-control passphrase-field',
        },
    )

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'min_length': 8,
            'max_length': 128,
            'label_suffix': '*',
        })
        super().__init__(*args, **kwargs)
