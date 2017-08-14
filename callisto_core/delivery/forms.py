import logging

from nacl.exceptions import CryptoError

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory

from . import validators
from .models import Report

logger = logging.getLogger(__name__)


def passphrase_field(label):
    return forms.CharField(
        max_length=64,
        label=label,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',
            'class': 'form-control',
        }),
    )


class ReportBaseForm(forms.models.ModelForm):
    key = passphrase_field('Passphrase')

    class Meta:
        model = Report
        fields = []


class ReportCreateForm(ReportBaseForm):
    message_confirmation_error = "key and key confirmation must match"
    key_confirmation = passphrase_field('Confirm Passphrase')

    def clean_key_confirmation(self):
        key = self.cleaned_data.get("key")
        key_confirmation = self.cleaned_data.get("key_confirmation")
        if key != key_confirmation:
            raise forms.ValidationError(self.message_confirmation_error)


class ReportAccessForm(ReportBaseForm):
    message_key_error = 'invalid secret key'
    message_key_error_log = 'decryption failure on {}'

    @property
    def report(self):
        return self.instance

    def clean_key(self):
        try:
            self._decrypt_report()
        except CryptoError:
            self._decryption_failed()

    def _decrypt_report(self):
        self.decrypted_report = self.report.decrypted_report(
            self.data['key'])

    def _decryption_failed(self):
        logger.info(self.message_key_error_log.format(self.report))
        raise forms.ValidationError(self.message_key_error)


class SubmitReportToAuthorityForm(forms.Form):
    name = forms.CharField(label="Your preferred first name:",
                           required=False,
                           max_length=500,
                           widget=forms.TextInput(attrs={'placeholder': 'ex. Chris'}),)

    phone_number = forms.CharField(label="Preferred phone number to call:",
                                   required=True,
                                   max_length=50,
                                   widget=forms.TextInput(attrs={'placeholder': 'ex. (555) 555-5555'}),)

    voicemail = forms.CharField(
        label="Is it ok to leave a voicemail? If so, what would you like the message to refer to?",
        required=False,
        max_length=256,
        widget=forms.TextInput(
            attrs={
                'placeholder': "ex. Yes, please just say you're following up from Callisto."}),
    )

    email = forms.EmailField(label="If you can't be reached by phone, what's the best email address to reach you?",
                             required=True,
                             max_length=256,
                             widget=forms.TextInput(attrs={'placeholder': 'ex. myname@gmail.com'}),)

    contact_notes = forms.CharField(
        label="Any notes on what time of day is best to reach you? A {0} staff member will "
        "try their best to accommodate your needs.".format(
            settings.SCHOOL_SHORTNAME), required=False, widget=forms.Textarea(
            attrs={
                'placeholder': "ex. I have class from 9-2 most weekdays and work in the evenings,"
                               " so mid afternoon is best (around 2:30-5pm)."
                " Wednesdays and Thursdays I have class the entire day, so those days don't work at all.",
                'max_length': 5000}),)

    email_confirmation = forms.ChoiceField(
        choices=[(True, "Yes"),
                 (False, "No, thanks")],
        label="Would you like us to send you a confirmation email with information about your rights in the reporting "
              "process, and where to get support and find resources on campus?",
        required=True,
        widget=forms.RadioSelect)

    def __init__(self, user, report, *args, **kwargs):
        super(SubmitReportToAuthorityForm, self).__init__(*args, **kwargs)
        self.user = user
        self.report = report
        self.fields['key'].widget.attrs['placeholder'] = 'ex. I am a muffin baking ninja'

        # TODO: populate these intelligently if we have the data elsewhere (in match reports, other reports)
        self.fields['name'].initial = report.contact_name
        self.fields['phone_number'].initial = report.contact_phone
        self.fields['voicemail'].initial = report.contact_voicemail
        self.fields['email'].initial = report.contact_email or user.email
        self.fields['contact_notes'].initial = report.contact_notes


def join_list_with_or(lst):
    if len(lst) < 2:
        return lst[0]
    all_but_last = ', '.join(lst[:-1])
    last = lst[-1]
    return ' or '.join([all_but_last, last])


class SubmitToMatchingForm(forms.Form):

    '''
        designed to be overridden if more complicated assignment of matching validators is needed
    '''

    def get_validators(self):
        return getattr(settings, 'CALLISTO_IDENTIFIER_DOMAINS', validators.facebook_only)

    def __init__(self, *args, **kwargs):
        super(SubmitToMatchingForm, self).__init__(*args, **kwargs)

        self.identifier_domain_info = self.get_validators()

        self.formatted_identifier_descriptions = join_list_with_or(list(self.identifier_domain_info))
        self.formatted_identifier_descriptions_title_case = join_list_with_or(
            [identifier.title() for identifier in list(self.identifier_domain_info)])

        self.formatted_example_identifiers = join_list_with_or([identifier_info['example'] for _, identifier_info in
                                                                self.identifier_domain_info.items()])

        self.fields['perp_name'] = forms.CharField(label="Perpetrator's Name",
                                                   required=False,
                                                   max_length=500,
                                                   widget=forms.TextInput(
                                                       attrs={
                                                           'placeholder': 'ex. John Jacob Jingleheimer Schmidt'}))

        self.fields['perp'] = forms.CharField(
            label="Perpetrator's {}".format(
                self.formatted_identifier_descriptions_title_case),
            required=True,
            max_length=500,
            widget=forms.TextInput(
                attrs={
                    'placeholder': 'ex. {}'.format(
                        self.formatted_example_identifiers)}))

    def clean_perp(self):
        raw_url = self.cleaned_data.get('perp').strip()
        for _, identifier_info in self.identifier_domain_info.items():
            try:
                matching_identifier = identifier_info['validation'](raw_url)
                if matching_identifier:
                    prefix = identifier_info['unique_prefix']
                    if len(prefix) > 0:  # Facebook has an empty unique identifier for backwards compatibility
                        matching_identifier = prefix + ":" + matching_identifier  # FB URLs can't contain colons
                    return matching_identifier
            except Exception as e:
                if e.__class__ is not ValidationError:
                    logger.exception(e)
                pass
        # no valid identifier found
        raise ValidationError('Please enter a valid {}.'.format(self.formatted_identifier_descriptions),
                              code='invalidmatchidentifier')


SubmitToMatchingFormSet = formset_factory(SubmitToMatchingForm, extra=0, min_num=1)
