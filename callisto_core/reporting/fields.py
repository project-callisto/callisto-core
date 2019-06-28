from django import forms
from django.core.exceptions import ValidationError


class MatchIdentifierField(forms.CharField):
    def __init__(self, *args, matching_validators, **kwargs):
        self.matching_validators = matching_validators
        kwargs.update({"label": self.matching_validators.titled()})
        self.widget = forms.TextInput(
            attrs={"placeholder": self.matching_validators.examples()}
        )
        super().__init__(*args, **kwargs)

    def _clean_with_identifier_validators(self, value):
        if not value:
            return value
        matching_id = self.matching_validators.validator["validation_function"](value)
        if matching_id:
            prefix = self.matching_validators.validator["unique_prefix"]
            # Facebook has an empty unique identifier
            # for backwards compatibility
            if len(prefix) > 0:
                # FB URLs can't contain colons
                matching_id = prefix + ":" + matching_id
            return matching_id
        else:
            raise ValidationError(self.matching_validators.invalid())

    def clean(self, value):
        value = super().clean(value)
        value = self._clean_with_identifier_validators(value)
        return value
