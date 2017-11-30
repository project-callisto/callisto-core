from django import forms

    #TODO something likely has to be passed into here in place of object
class Field(object):
    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text='', error_messages=None, show_hidden_initial=False,
                 validators=(), localize=False, disabled=False, label_suffix=None):

        self.required, self.label, self.initial = required, label, initial

        if self.required is True:
            self.label_suffix = '*'
        elif label_suffix is not None:
            self.label_suffix = label_suffix
        else:
            self.label_suffix = _('')

        super(Field, self).__init__()


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
        })
        super().__init__(*args, **kwargs)
