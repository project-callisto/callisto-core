import logging
from collections import OrderedDict
from hashlib import sha256

import bcrypt

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
from django.utils.safestring import mark_safe

from callisto_core.utils.api import NotificationApi, TenantApi

from . import auth, models, validators

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

    def get_users(self, email):
        '''Get users that would match the email passed in.

        Updated to support the encrypted login format created during 2019
        Summer Maintenance.
        '''
        email = sha256(email.encode('utf-8')).hexdigest()
        email_index = auth.index(email)

        active_users = models.Account.objects.filter(**{
            'email_index': email_index,
        })

        return (User.objects.get(pk=u.user_id) 
            for u in active_users 
            if bcrypt.checkpw(
                email.encode('utf-8'), u.encrypted_email.encode('utf-8')))

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
            min_length=settings.PASSWORD_MIN_LENGTH,
            max_length=settings.PASSWORD_MAX_LENGTH,
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


class ReportingVerificationEmailForm(
    PasswordResetForm,
):

    def __init__(self, *args, school_email_domain, **kwargs):
        self.school_email_domain = school_email_domain
        if kwargs.get('instance'):  # TODO: remove
            kwargs.pop('instance')
        if kwargs.get('view'):  # TODO: remove
            kwargs.pop('view')
        super().__init__(*args, **kwargs)
        email_field = self.fields['email']
        email_field.label = "Your school email"
        email_field.label_suffix = '*'
        email_field.widget.attrs.update(**self.create_placeholder())

    def create_placeholder(self):
        return {'placeholder': ', '.join(
            ['myname@' + x for x in self.school_email_domain.split(',')],
        )}

    def clean_email(self):
        validators.validate_school_email(
            self.data.get('email'),
            self.school_email_domain,
        )
        return self.data.get("email")
