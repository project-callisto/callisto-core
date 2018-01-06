'''

Views specific to callisto-core, if you are implementing callisto-core
you SHOULD NOT be importing these views. Import from view_partials instead.
All of the classes in this file should represent one of more HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

views should define:
    - templates

'''
from . import view_partials


class SignupView(
    view_partials.SignupPartial,
):
    template_name = 'callisto_core/accounts/signup.html'


class LoginView(
    view_partials.LoginPartial,
):
    template_name = 'callisto_core/accounts/login.html'


class PasswordResetView(
    view_partials.PasswordResetPartial,
):
    template_name = 'callisto_core/accounts/password_reset.html'
    email_template_name = 'callisto_core/accounts/password_reset_email.html'


class LogoutView(
    view_partials.LogoutPartial,
):
    pass
