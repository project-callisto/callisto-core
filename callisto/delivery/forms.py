import logging

from nacl.exceptions import CryptoError
from six.moves.urllib.parse import parse_qs, urlsplit
from zxcvbn import password_strength

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory

from callisto.evaluation.models import EvalRow

REQUIRED_ERROR = "The {0} field is required."

logger = logging.getLogger(__name__)


class NewSecretKeyForm(forms.Form):
    error_messages = {
        'key_mismatch': "The two passphrase fields didn't match.",
    }

    key = forms.CharField(max_length=64,
                           label="Your passphrase",
                           widget=forms.PasswordInput(attrs={'placeholder': 'Your passphrase',
                                                         'autocomplete': 'off'}),
                           error_messages = {'required': REQUIRED_ERROR.format("passphrase")})
    key2 = forms.CharField(max_length=64,
                           label="Repeat your passphrase",
                           widget=forms.PasswordInput(attrs={'placeholder': 'Repeat your passphrase',
                                                         'autocomplete': 'off'}),
                           error_messages = {'required': REQUIRED_ERROR.format("passphrase confirmation")})

    # from http://birdhouse.org/blog/2015/06/16/sane-password-strength-validation-for-django-with-zxcvbn/

    # Portions of the below implementation are copyright cca.edu, and are under the Educational Community License:
    # https://opensource.org/licenses/ECL-2.0

    def clean_key(self):
        # Password strength testing mostly done in JS; minimal validation here.
        password = self.cleaned_data.get('key')
        results = password_strength(password)

        if results['entropy'] < settings.PASSWORD_MINIMUM_ENTROPY:
            raise forms.ValidationError("Your password isn't strong enough.")
        return password


    def clean_key2(self):
        key1 = self.cleaned_data.get("key")
        key2 = self.cleaned_data.get("key2")
        if key1 and key2 and key1 != key2:
            raise forms.ValidationError(
                self.error_messages['key_mismatch'],
                code='key_mismatch',
            )
        return key2

class SecretKeyForm(forms.Form):
    error_messages = {
        'wrong_key': "The passphrase didn't match.",
    }

    key = forms.CharField(max_length=254,
                          label="Your passphrase",
                          widget=forms.PasswordInput(attrs={'placeholder': 'Your passphrase',
                                                        'autocomplete': 'off'}),
                          error_messages = {'required': REQUIRED_ERROR.format("passphrase")})

    def clean_key(self):
        key = self.cleaned_data.get('key')
        report = self.report
        try:
            decrypted_report = report.decrypted_report(key)
            self.decrypted_report = decrypted_report
            #save anonymous row if one wasn't saved on creation
            try:
                row = EvalRow()
                row.set_identifiers(report)
                if (EvalRow.objects.filter(record_identifier = row.record_identifier).count() == 0):
                    row.action = EvalRow.FIRST
                    row.add_report_data(decrypted_report)
                    row.save()
            except Exception as e:
                logger.error(e)
                pass
        except CryptoError:
            self.decrypted_report = None
            raise forms.ValidationError(
                self.error_messages['wrong_key'],
                code='wrong_key',
            )
        return key


class SubmitToSchoolForm(SecretKeyForm):
    name = forms.CharField(label="Your preferred first name:",
                                    required=False,
                                    max_length=500,
                                    widget=forms.TextInput(attrs={'placeholder': 'ex. Chris'}),)

    phone_number = forms.CharField(label="Preferred phone number to call:",
                                    required=True,
                                    max_length=50,
                                    widget=forms.TextInput(attrs={'placeholder': 'ex. (555) 555-5555'}),)

    voicemail = forms.CharField(label="Is it ok to leave a voicemail? If so, what would you like the message to refer to?",
                                    required=False,
                                    max_length=256,
                                    widget=forms.TextInput(attrs={'placeholder': "ex. Yes, please just say you're following up from Callisto."}),)

    email = forms.EmailField(label="If you can't be reached by phone, what's the best email address to reach you?",
                                    required=True,
                                    max_length=256,
                                    widget=forms.TextInput(attrs={'placeholder': 'ex. myname@gmail.com'}),)

    contact_notes = forms.CharField(label="Any notes on what time of day is best to reach you? A {0} staff member will "
                                          "try their best to accommodate your needs.".format(settings.SCHOOL_SHORTNAME),
                                    required=False,
                                    widget=forms.Textarea(attrs={'placeholder': "ex. I have class from 9-2 most weekdays and work in the evenings, so mid afternoon is best (around 2:30-5pm)."
                                                                                "Wednesdays and Thursdays I have class the entire day, so those days don't work at all.",
                                                                 'max_length': 5000}),)

    email_confirmation = forms.ChoiceField(choices=[(True, "Yes"), (False, "No, thanks")],
                                           label="Would you like us to send you a confirmation email with information about your rights in the reporting process, and where to get support and find resources on campus?",
                                           required=True,
                                           widget=forms.RadioSelect)

    def __init__(self, user, report, *args, **kwargs):
        super(SecretKeyForm, self).__init__(*args, **kwargs)
        self.user = user
        self.report = report
        self.fields['key'].widget.attrs['placeholder'] = 'ex. I am a muffin baking ninja'

        #TODO: populate these intelligently if we have the data elsewhere (in match reports, other reports)
        self.fields['name'].initial = report.contact_name
        self.fields['phone_number'].initial = report.contact_phone
        self.fields['voicemail'].initial = report.contact_voicemail
        self.fields['email'].initial = report.contact_email or user.email
        self.fields['contact_notes'].initial = report.contact_notes

class SubmitToMatchingForm(forms.Form):
    perp_name = forms.CharField(label="Perpetrator's Name",
                            required=False,
                            max_length=500,
                            widget=forms.TextInput(attrs={'placeholder': 'ex. John Jacob Jingleheimer Schmidt',}),)

    perp = forms.URLField(label="Perpetrator's Facebook URL",
                            required=True,
                            max_length=500,
                            widget=forms.TextInput(attrs={'placeholder': 'ex. http://www.facebook.com/johnsmithfakename'}),)

    def clean_perp(self):
        raw_url = self.cleaned_data.get('perp')
        url_parts = urlsplit(raw_url)
        #check if Facebook
        domain = url_parts[1]
        if not (domain=='facebook.com' or domain.endswith('.facebook.com')):
            raise ValidationError('Please enter a valid Facebook profile URL.', code='notfacebook')
        path = url_parts[2].strip('/').split('/')[0]
        generic_fb_urls = ['messages', 'hashtag', 'events', 'pages', 'groups', 'bookmarks', 'lists', 'developers', 'topic', 'help',
                           'privacy', 'campaign', 'policies', 'support', 'settings', 'games']
        if path == "profile.php":
            path = parse_qs(url_parts[3]).get('id')[0]
        if not path or path == "" or path.endswith('.php') or path in generic_fb_urls:
            raise ValidationError('Please enter a valid Facebook profile URL.', code='notfacebook')
        else:
            return path

SubmitToMatchingFormSet = formset_factory(SubmitToMatchingForm, extra=0, min_num=1)
