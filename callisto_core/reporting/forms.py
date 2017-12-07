import json
import logging

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.core.urlresolvers import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from callisto_core.delivery import (
    fields as delivery_fields, forms as delivery_forms,
    models as delivery_models,
)
from callisto_core.utils.api import NotificationApi, TenantApi
from callisto_core.utils.forms import NoRequiredLabelMixin

from . import fields, report_delivery, tokens, validators

logger = logging.getLogger(__name__)


class SendVerificationEmailForm(
    NoRequiredLabelMixin,
    PasswordResetForm,
):
    # only used for testing currently

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            kwargs.pop('instance')
        self.view = kwargs.pop('view')
        super().__init__(*args, **kwargs)
        self.fields['email'].label = "Your school email"
        self.fields['email'].widget.attrs.update(self.email_field_placeholder)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validators.validate_school_email(email, request=self.view.request)
        return email

    def send_mail(self):
        pass  # TODO

    def save(self, *args, **kwargs):
        self.send_mail()

    def get_users(self, email):
        return[self.view.request.user]

    def email_field_placeholder(self):
        school_email_domain = TenantApi.site_settings(
            'SCHOOL_EMAIL_DOMAIN',
            request=self.view.request,
        )
        return {'placeholder': ', '.join(
            ['myname@' + x for x in school_email_domain.split(',')],
        )},


class ReportingVerificationEmailForm(
    SendVerificationEmailForm,
):
    token_generator = tokens.StudentVerificationTokenGenerator()

    def send_mail(self):
        self.redirect_url = self._get_confirmation_url()
        NotificationApi.send_student_verification_email(self)

    def _get_confirmation_url(self):
        uidb64 = urlsafe_base64_encode(
            force_bytes(self.view.request.user.pk)).decode("utf-8")
        token = self.token_generator.make_token(self.view.request.user)
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={
                'uuid': self.view.report.uuid,
                'uidb64': uidb64,
                'token': token,
            },
        )


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
        widget=forms.TextInput(attrs={'placeholder': 'ex. John Doe'}),
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
    key = delivery_fields.PassphraseField(label='Passphrase')
    field_order = [
        'confirmation',
        'key',
    ]

    def clean_key(self):
        if not self.data.get('key') == self.view.storage.passphrase:
            forms.ValidationError('Invalid key')

    class Meta:
        model = delivery_models.SentFullReport
        fields = []
