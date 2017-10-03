from django import forms
from django.core.exceptions import ValidationError


class MatchIdentifierField(forms.CharField):

    def __init__(self, *args, validators, **kwargs):
        self.validators = validators
        kwargs.update({
            'label': self.validators.titled(),
        })
        self.widget = forms.TextInput(
            attrs={'placeholder': self.validators.examples()}
        )
        super().__init__(*args, **kwargs)

    def _clean_with_identifier_validators(self, value):
        if not value:
            return value
        for identifier_info in self.validators.value():
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
            raise ValidationError(self.validators.invalid())

    def clean(self, value):
        value = super().clean(value)
        value = self._clean_with_identifier_validators(value)
        return value
