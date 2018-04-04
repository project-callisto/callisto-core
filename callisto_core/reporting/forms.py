import json
import logging

from django import forms

from callisto_core.delivery import (
    forms as delivery_forms, models as delivery_models,
)
from callisto_core.utils.forms import NoRequiredLabelMixin

from . import fields, report_delivery, validators

logger = logging.getLogger(__name__)


class PrepForm(
    NoRequiredLabelMixin,
    delivery_forms.FormViewExtensionMixin,
    forms.models.ModelForm,
):
    contact_name = forms.CharField(
        label="First Name",
        required=False,
    )
    contact_email = forms.CharField(
        label="Email Address",
        required=True,
    )
    contact_phone = forms.CharField(
        label="Phone Number",
        required=True,
    )
    contact_notes = forms.ChoiceField(
        choices=[
            ('Morning', 'Morning'),
            ('Afternoon', 'Afternoon'),
            ('Evening', 'Evening'),
            ('No Preference', 'No Preference'),
        ],
        label='What is the best time to reach you?',
        widget=forms.RadioSelect,
        required=False,
    )
    contact_voicemail = forms.BooleanField(
        label='Is it okay if your school leaves a voicemail?',
        required=False,
    )

    class Meta:
        model = delivery_models.Report
        fields = [
            'contact_name',
            'contact_email',
            'contact_phone',
            'contact_notes',
            'contact_voicemail',
        ]


class ReportSubclassBaseForm(
    NoRequiredLabelMixin,
    delivery_forms.FormViewExtensionMixin,
    forms.models.ModelForm,
):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.report = self.view.report


class MatchingBaseForm(
    ReportSubclassBaseForm,
):
    perp_name = forms.CharField(
        label="Perpetrator's Name",
        required=False,
        widget=forms.TextInput(),
    )

    def __init__(self, *args, matching_validators=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not matching_validators:
            self.matching_validators = validators.Validators()
        else:
            self.matching_validators = matching_validators
        self.fields['identifier'] = fields.MatchIdentifierField(
            required=self.matching_field_required,
            matching_validators=self.matching_validators,
        )

    def save(self, commit=True):
        if self.data.get('identifier'):
            super().save(commit=commit)

            report_content = report_delivery.MatchReportContent.from_form(self)
            self.instance.encrypt_match_report(
                report_text=json.dumps(report_content.__dict__),
                identifier=self.cleaned_data.get('identifier'),
            )

            return self.instance
        else:
            return None


class MatchingOptionalForm(
    MatchingBaseForm,
):
    matching_field_required = False

    class Meta:
        model = delivery_models.MatchReport
        fields = []


class MatchingRequiredForm(
    MatchingBaseForm,
):
    matching_field_required = True

    class Meta:
        model = delivery_models.MatchReport
        fields = []


class ConfirmationForm(
    ReportSubclassBaseForm,
):
    confirmation = forms.BooleanField(
        label="Yes, I agree and I understand",
        initial=False,
        required=True,
    )

    class Meta:
        model = delivery_models.SentFullReport
        fields = []
