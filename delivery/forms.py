from django import forms
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.conf import settings
from urllib.parse import urlsplit, parse_qs

from account.forms import SecretKeyForm

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

    email_confirmation = forms.ChoiceField(choices = [(True, "Yes"), (False, "No, thanks")],
                                           label="Would you like us to send you a confirmation email with information about your rights in the reporting process, and where to get support and find resources on campus?",
                                           required=True,
                                           widget = forms.RadioSelect)

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
