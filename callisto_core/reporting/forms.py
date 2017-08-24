import json
import logging

from django import forms
from django.conf import settings

from . import report_delivery
from ..delivery import forms as delivery_forms, models as delivery_models
from .validators import Validators

logger = logging.getLogger(__name__)


def identifier_field(required):
    return forms.CharField(
        label=Validators.titled(),
        required=required,
        widget=forms.TextInput(attrs={'placeholder': Validators.examples()}),
    )


class PrepForm(
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
        initial='No Preference',
        widget=forms.RadioSelect,
    )
    contact_voicemail = forms.BooleanField(
        label='Is it okay if your school leaves a voicemail?',
        initial=True,
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
        widget=forms.TextInput(attrs={'placeholder': 'ex. John Doe'}),
    )

    def clean_identifier(self):
        identifier = self.cleaned_data.get('identifier').strip()
        for identifier_info in Validators.value():
            try:
                matching_id = identifier_info['validation'](identifier)
                if matching_id:
                    prefix = identifier_info['unique_prefix']
                    # Facebook has an empty unique identifier
                    # for backwards compatibility
                    if len(prefix) > 0:
                        # FB URLs can't contain colons
                        matching_id = prefix + ":" + matching_id
                    return matching_id
            except Exception as e:
                if e.__class__ is not forms.ValidationError:
                    logger.exception(e)
                pass
        # no valid identifier found
        raise forms.ValidationError(Validators.invalid())

    def save(self, commit=True):
        output = super().save(commit=commit)

        report_content = report_delivery.MatchReportContent.from_form(self)
        self.instance.encrypt_match_report(
            report_text=json.dumps(report_content.__dict__),
            key=self.cleaned_data.get('identifier'),
        )

        return output

    class Meta:
        model = delivery_models.MatchReport
        fields = ['identifier']


class MatchingOptionalForm(
    MatchingBaseForm,
):
    identifier = identifier_field(required=False)


class MatchingRequiredForm(
    MatchingBaseForm,
):
    identifier = identifier_field(required=True)


class ConfirmationForm(
    ReportSubclassBaseForm,
):
    key = delivery_forms.passphrase_field('Passphrase')
    confirmation = forms.BooleanField(
        label="Yes, I agree and I understand",
        initial=False,
        required=True,
    )

    def clean_key(self):
        if not self.data.get('key') == self.view.storage.secret_key:
            forms.ValidationError('Invalid key')

    def save(self, commit=True):
        self.instance.to_address = settings.COORDINATOR_EMAIL
        return super().save(commit=commit)

    class Meta:
        model = delivery_models.SentFullReport
        fields = []
