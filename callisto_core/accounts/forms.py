import logging
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.forms.widgets import PasswordInput, TextInput
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.safestring import mark_safe

from callisto_core.accounts.tokens import StudentVerificationTokenGenerator
from callisto_core.utils.api import NotificationApi, TenantApi

from . import validators

User = get_user_model()
logger = logging.getLogger(__name__)

TERMS_NOT_ACCEPTED_ERROR = "You have to accept the terms of service to register with Callisto."
REQUIRED_ERROR = "The {0} field is required."


class LoginForm(AuthenticationForm):
    username = CharField(
        max_length=30,
        label='Username',
        error_messages={'required': REQUIRED_ERROR.format("username")},
    )
    password = CharField(
        max_length=64,
        label="Password",
        widget=PasswordInput(),
        error_messages={'required': REQUIRED_ERROR.format("password")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if TenantApi.site_settings(
            'DISABLE_SIGNUP',
            cast=bool,
            request=self.request,
        ):
            label = 'Email Address'
        else:
            label = 'Username'
        self.fields['username'] = CharField(
            max_length=64,
            label=label,
            error_messages={'required': REQUIRED_ERROR.format(label)},
        )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        current_site_id = self.request.site.id
        if user.account.site_id is not current_site_id:
            error_msg = 'user site_id not matching in login request'
            if settings.DEBUG:
                logger.error(error_msg)
            else:
                logger.warn(error_msg)
            raise ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )


class SignUpForm(UserCreationForm):

    username = CharField(
        label='Username',
        widget=TextInput(attrs={
            'class': 'show-requirements',
            'data-requirement': 'required',
        }),
        error_messages={
            'required': REQUIRED_ERROR.format("username"),
            'unique': "Username invalid. Please try another.",
        },
    )
    password1 = CharField(
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
        label="Password",
        widget=PasswordInput(attrs={
            'class': 'show-requirements',
            'data-requirement': 'password',
        }),
        error_messages={'required': REQUIRED_ERROR.format("password")},
    )
    password2 = CharField(
        widget=PasswordInput(attrs={
            'class': 'show-requirements',
            'data-requirement': 'password-confirmation',
        }),
        label="Confirm password",
        error_messages={
            'required': REQUIRED_ERROR.format("password confirmation"),
        },
    )
    email = forms.EmailField(
        required=False,
        label='Optional email',
        help_text=mark_safe('''
            Your email is only used to reset your password if you lose it.
        '''),
    )
    terms = forms.BooleanField(
        required=True,
        label=mark_safe('''
            I have read and agree to Callisto\'s Terms and Privacy Policy
        '''),
        help_text=mark_safe('''
            We care deeply about your privacy, and know you do too.
            Your information will remain completely private until you choose otherwise.
            Read more in Callisto's
            <a href="/about/our-policies/#terms-of-service" target="_blank">
            Terms</a> and
            <a href="/about/our-policies/#privacy-policy" target="_blank">
            Privacy Policy</a>.
        '''),
        error_messages={
            'required': TERMS_NOT_ACCEPTED_ERROR,
        },
    )

    class Meta:
        model = User
        fields = ("username", 'password1', 'password2', "email",)


class FormattedPasswordResetForm(PasswordResetForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = "Enter your email to reset your password"

    def save(self, *args, **kwargs):
        kwargs['domain_override'] = TenantApi.get_current_domain()
        super().save(*args, **kwargs)

    def send_mail(self, *args, **kwargs):
        NotificationApi.send_password_reset_email(self, *args, **kwargs)


class CustomSetPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'] = CharField(
            max_length=64,
            min_length=8,
            label=self.password1_label,
            widget=PasswordInput(),
            error_messages={'required': REQUIRED_ERROR.format("password")},
        )


class FormattedSetPasswordForm(CustomSetPasswordForm):
    password1_label = "Enter your new password"


class ActivateSetPasswordForm(CustomSetPasswordForm):
    password1_label = "Password"


class FormattedPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'] = CharField(
            max_length=64,
            label="Enter your new password",
            widget=PasswordInput(),
            error_messages={'required': REQUIRED_ERROR.format("password")},
        )
        self.fields['new_password2'].label = "Confirm new password"
        self.fields['old_password'].label = "Old password"


# in original PasswordChangeForm file to reorder fields
FormattedPasswordChangeForm.base_fields = OrderedDict(
    (k, PasswordChangeForm.base_fields[k])
    for k in ['old_password', 'new_password1', 'new_password2']
)


class SendVerificationEmailForm(
    PasswordResetForm,
):
    # only used for testing currently

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            kwargs.pop('instance')
        self.view = kwargs.pop('view')
        super().__init__(*args, **kwargs)
        email_field = self.fields['email']
        email_field.label = "Your school email"
        email_field.label_suffix = '*'
        email_field.widget.attrs.update(**self.email_field_placeholder())

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validators.validate_school_email(email, request=self.view.request)
        return email

    def send_mail(self):
        pass

    def get_users(self, email):
        return[self.view.request.user]

    def email_field_placeholder(self):
        school_email_domain = TenantApi.site_settings(
            'SCHOOL_EMAIL_DOMAIN',
            request=self.view.request,
        )
        return {'placeholder': ', '.join(
            ['myname@' + x for x in school_email_domain.split(',')],
        )}

    def save(self, *args, **kwargs):
        account = self.view.request.user.account
        account.school_email = self.cleaned_data["email"]
        account.save()
        self.send_mail()


class ReportingVerificationEmailForm(
    SendVerificationEmailForm,
):
    token_generator = StudentVerificationTokenGenerator()

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
