import json
import logging

from django import forms

from callisto_core.delivery import forms as delivery_forms, models as delivery_models
from callisto_core.utils.forms import NoRequiredLabelMixin

from . import fields, report_delivery, validators

logger = logging.getLogger(__name__)


class PrepForm(
    NoRequiredLabelMixin, delivery_forms.FormViewExtensionMixin, forms.models.ModelForm
):
    contact_name = forms.CharField(label="First Name", required=False)
    contact_email = forms.CharField(label="Email Address", required=True)
    contact_phone = forms.CharField(label="Phone Number", required=True)
    contact_notes = forms.ChoiceField(
        choices=[
            ("Morning", "Morning"),
            ("Afternoon", "Afternoon"),
            ("Evening", "Evening"),
            ("No Preference", "No Preference"),
        ],
        label="What is the best time to reach you?",
        widget=forms.RadioSelect,
        required=False,
    )
    contact_voicemail = forms.BooleanField(
        label="Is it okay if your school leaves a voicemail?", required=False
    )


class ReportSubclassBaseForm(
    NoRequiredLabelMixin, delivery_forms.FormViewExtensionMixin, forms.models.ModelForm
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.report = self.view.report


class MatchingBaseForm(ReportSubclassBaseForm):
    perp_name = forms.CharField(
        label="Perpetrator's Name", required=False, widget=forms.TextInput()
    )

    def __init__(self, *args, matching_validators=None, **kwargs):
        super().__init__(*args, **kwargs)
        perp_identifiers = validators.perp_identifiers()
        for identifier_type in perp_identifiers:
            field_name = "%s_identifier" % (perp_identifiers[identifier_type]["id"])
            self.fields[field_name] = fields.MatchIdentifierField(
                required=False,
                matching_validators=validators.Validators(
                    perp_identifiers[identifier_type]
                ),
            )

    def clean(self):
        identifiers = set()
        identifier_type = ""
        identifier_types = validators.perp_identifiers()
        from django.core.exceptions import ValidationError

        for identifier_type in identifier_types:
            i = 0
            field_name = "%s_identifier_%s" % (identifier_type, i)

            while self.data.get(field_name):
                identifier = self.data.get(field_name)
                identifier = identifier_types[identifier_type]["validation_function"](
                    identifier
                )
                if identifier_types[identifier_type]["unique_prefix"]:
                    identifier = (
                        identifier_types[identifier_type]["unique_prefix"]
                        + ":"
                        + identifier
                    )
                if identifier:
                    identifiers.add(identifier)
                else:
                    raise ValidationError(
                        ("Invalid %(id_type)s"),
                        code="invalid",
                        params={"id_type": identifier_types[identifier_type]["id"]},
                    )
                i += 1
                field_name = "%s_identifier_%s" % (identifier_type, i)

            field_name = "%s_identifier" % (identifier_type)
            if self.data.get(field_name):
                identifier = self.data[field_name]
                identifiers.add(identifier)
                field_name = "%s_identifier" % (identifier_type)

        self.cleaned_data["identifiers"] = identifiers

    def save(self, commit=True):
        identifiers = self.cleaned_data["identifiers"]
        if identifiers:
            super().save(commit=commit)
            for identifier in identifiers:
                report_content = report_delivery.MatchReportContent.from_form(self)
                self.instance.encrypt_match_report(
                    report_text=json.dumps(report_content.__dict__),
                    identifier=identifier,
                )
            return self.instance
        else:
            return None


class MatchingOptionalForm(MatchingBaseForm):
    class Meta:
        model = delivery_models.MatchReport
        fields = []


class MatchingRequiredForm(MatchingBaseForm):
    class Meta:
        model = delivery_models.MatchReport
        fields = []


class ConfirmationForm(ReportSubclassBaseForm):
    confirmation = forms.BooleanField(
        label="Yes, I agree and I understand", initial=False, required=True
    )

    class Meta:
        model = delivery_models.SentFullReport
        fields = []


class ConfirmedConfirmationForm(ReportSubclassBaseForm):
    confirmation = forms.BooleanField(
        label="Yes, I agree and I understand", initial=True, required=True
    )

    class Meta:
        model = delivery_models.SentFullReport
        fields = []
