from django import forms
from django.core.exceptions import ValidationError

from .validators import Validators


class MatchIdentifierField(forms.CharField):
    widget = forms.TextInput(
        attrs={'placeholder': Validators.examples()}
    )

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'label': Validators.titled(),
        })
        super().__init__(*args, **kwargs)

    def _clean_with_identifier_validators(self, value):
        for identifier_info in Validators.value():
            matching_id = identifier_info['validation'](value)
            if matching_id:
                prefix = identifier_info['unique_prefix']
                # Facebook has an empty unique identifier
                # for backwards compatibility
                if len(prefix) > 0:
                    # FB URLs can't contain colons
                    matching_id = prefix + ":" + matching_id
                return matching_id
        else:
            raise ValidationError(Validators.invalid())

    def clean(self, value):
        value = super().clean(value)
        value = self._clean_with_identifier_validators(value)
        return value
