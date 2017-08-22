from django import forms
from django.conf import settings

from . import validators
from ..delivery import forms as delivery_forms, models as delivery_models


class ReportingForm(
    delivery_forms.FormViewExtensionMixin,
    forms.models.ModelForm,
):
    contact_name = forms.CharField(
        label="Your preferred first name:",
        widget=forms.TextInput(
            attrs={'placeholder': 'ex. Chris'},
        ),
    )
    contact_phone = forms.CharField(
        label="Preferred phone number to call:",
        widget=forms.TextInput(
            attrs={'placeholder': 'ex. (555) 555-5555'}
        ),
    )
    contact_voicemail = forms.CharField(
        label="Is it ok to leave a voicemail? If so, what would you like the message to refer to?",
        widget=forms.TextInput(
            attrs={
                'placeholder': "ex. Yes, please just say you're following up from Callisto."},
        ),
    )
    contact_email = forms.EmailField(
        label="If you can't be reached by phone, what's the best email address to reach you?",
        widget=forms.TextInput(
            attrs={'placeholder': 'ex. myname@gmail.com'},),)
    contact_notes = forms.CharField(
        label='''
            Any notes on what time of day is best to reach you?
            A {0} staff member will try their best to accommodate
            your needs.
        '''.format(settings.SCHOOL_SHORTNAME),
        widget=forms.Textarea(
            attrs={
                'placeholder': '''
                    ex. I have class from 9-2 most weekdays and work in
                    the evenings, so mid afternoon is best (around 2:30-5pm).
                    Wednesdays and Thursdays I have class the entire day,
                    so those days don't work at all.
                ''',
            },
        ),
    )
    email_confirmation = forms.ChoiceField(
        choices=[
            (True, "Yes"),
            (False, "No, thanks"),
        ],
        label='''
            Would you like us to send you a confirmation email
            with information about your rights in the reporting
            process, and where to get support and find resources on campus?
        ''',
        widget=forms.RadioSelect,
    )

    def clean_email_confirmation(self):
        if strtobool(self.data.get('email_confirmation')):
            api.NotificationApi.send_user_notification(
                self, 'submit_confirmation', self.view.site_id)

    class Meta:
        model = delivery_models.Report
        fields = [
            'contact_name',
            'contact_phone',
            'contact_voicemail',
            'contact_email',
            'contact_notes',
        ]


def join_list_with_or(lst):
    if len(lst) < 2:
        return lst[0]
    all_but_last = ', '.join(lst[:-1])
    last = lst[-1]
    return ' or '.join([all_but_last, last])


class SubmitToMatchingForm(forms.Form):
    '''
        designed to be overridden if more complicated
        assignment of matching validators is needed
    '''

    def get_validators(self):
        return getattr(
            settings,
            'CALLISTO_IDENTIFIER_DOMAINS',
            validators.facebook_only,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.identifier_domain_info = self.get_validators()

        self.formatted_identifier_descriptions = join_list_with_or(
            list(self.identifier_domain_info))

        _identifier_titles = []
        for identifier in list(self.identifier_domain_info):
            _identifier_titles.append(identifier.title())
        self.formatted_identifier_descriptions_title_case = join_list_with_or(
            _identifier_titles
        )

        self.formatted_example_identifiers = join_list_with_or(
            [
                identifier_info['example']
                for _, identifier_info in self.identifier_domain_info.items()
            ]
        )

        self.fields['perp_name'] = forms.CharField(
            label="Perpetrator's Name",
            required=False,
            max_length=500,
            widget=forms.TextInput(
                attrs={
                    'placeholder': 'ex. John Jacob Jingleheimer Schmidt',
                },
            ),
        )

        self.fields['perp'] = forms.CharField(
            label="Perpetrator's {}".format(
                self.formatted_identifier_descriptions_title_case,
            ),
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
                    if len(
                            prefix) > 0:  # Facebook has an empty unique identifier for backwards compatibility
                        matching_identifier = prefix + ":" + \
                            matching_identifier  # FB URLs can't contain colons
                    return matching_identifier
            except Exception as e:
                if e.__class__ is not forms.ValidationError:
                    logger.exception(e)
                pass
        # no valid identifier found
        raise forms.ValidationError(
            'Please enter a valid {}.'.format(
                self.formatted_identifier_descriptions),
            code='invalidmatchidentifier')
