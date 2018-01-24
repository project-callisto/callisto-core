'''

View partials provide all the callisto-core front-end functionality.
Subclass these partials with your own views if you are implementing
callisto-core. Many of the view partials only provide a subset of the
functionality required for a full HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

view_partials should define:
    - forms
    - models
    - helper classes
    - access checks
    - redirect handlers

and should not define:
    - templates
    - url names

'''
from django.contrib.auth import login, views as auth_views
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import is_safe_url
from django.views.generic import edit as edit_views

from callisto_core.utils.api import TenantApi

from . import forms, models


class SignupPartial(
    edit_views.CreateView,
):
    form_class = forms.SignUpForm
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if TenantApi.site_settings(
                'DISABLE_SIGNUP', cast=bool, request=request):
            return redirect(reverse('login'))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        next_page = self.request.GET.get('next', None)
        if next_page and is_safe_url(next_page, self.request.get_host()):
            return next_page
        else:
            return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        models.Account.objects.create(
            user=form.instance,
            site_id=self.request.site.id,
        )
        login(self.request, form.instance)
        return response


class LoginPartial(
    auth_views.LoginView,
):
    authentication_form = forms.LoginForm

    def get_template_names(self):
        if TenantApi.site_settings(
            'DISABLE_SIGNUP',
            cast=bool,
            request=self.request,
        ):
            self.template_name = self.signup_disabled_template_name
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        # IMPORTANT! this super call cannot be reduced to super()
        # TODO: add a test that fails with super()
        context = super(edit_views.FormView, self).get_context_data(**kwargs)
        current_site = self.request.site
        context.update({
            self.redirect_field_name: self.get_redirect_url(),
            'site': current_site,
            'site_name': current_site.name,
        })
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context


class PasswordResetPartial(
    auth_views.PasswordResetView,
):
    success_url = reverse_lazy('password_reset_sent')
    form_class = forms.FormattedPasswordResetForm


class PasswordChangePartial(
    auth_views.PasswordChangeView,
):
    form_class = forms.FormattedPasswordChangeForm
    success_url = reverse_lazy('dashboard')


class PasswordResetConfirmPartial(
    auth_views.PasswordResetConfirmView,
):
    form_class = forms.FormattedSetPasswordForm
    success_url = reverse_lazy('login')


class AccountActivationPartial(
    auth_views.PasswordResetConfirmView,
):
    form_class = forms.ActivateSetPasswordForm
    success_url = reverse_lazy('login')


class LogoutPartial(
    auth_views.LogoutView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = self.request.site
        context.update({
            'site': current_site,
            'site_name': current_site.name,
            'title': 'Logged out',
        })
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context
