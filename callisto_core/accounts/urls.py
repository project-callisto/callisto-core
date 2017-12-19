import django.contrib.auth.views as auth_views
from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from . import forms, views

urlpatterns = [
    url(r'^signup/$', views.CustomSignupView.as_view(), name='signup'),
    url(r'^login/$',
        view=views.CustomLoginView.as_view(),
        name='login',
        ),
    url(r'^logout/$', view=views.CustomLogoutView.as_view(), name='logout'),
    url(r'^change_password/$',
        view=auth_views.PasswordChangeView.as_view(
            template_name='password_change.html',
            success_url=reverse_lazy('dashboard'),
            form_class=forms.FormattedPasswordChangeForm,
        ),
        name='change_password',
        ),
    url(r'^forgot_password/$',
        view=views.CustomPasswordResetView.as_view(),
        name='reset',
        ),
    url(r'^forgot_password/sent/$',
        view=TemplateView.as_view(
            template_name="password_reset_sent.html",
        ),
        name='password_reset_sent',
        ),
    # TODO: DRY uid and token pattern
    url(r'^reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        view=auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            form_class=forms.FormattedSetPasswordForm,
            success_url=reverse_lazy('login'),
        ),
        name='reset_confirm',
        ),
    # TODO: DRY uid and token pattern
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        view=auth_views.PasswordResetConfirmView.as_view(
            template_name='account_activation_confirm.html',
            form_class=forms.ActivateSetPasswordForm,
            success_url=reverse_lazy('login'),
        ),
        name='activate_account',
        ),
]
