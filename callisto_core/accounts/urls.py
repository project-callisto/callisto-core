import django.contrib.auth.views as auth_views
from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from . import forms, views

urlpatterns = [
    url(r'^signup/',
        views.SignupView.as_view(),
        name='signup',
        ),
    url(r'^login/',
        view=views.LoginView.as_view(),
        name='login',
        ),
    url(r'^logout/',
        view=views.LogoutView.as_view(),
        name='logout',
        ),
    url(r'^change_password/',
        view=views.PasswordChangeView.as_view(),
        name='change_password',
        ),
    url(r'^forgot_password/',
        view=views.PasswordResetView.as_view(),
        name='reset',
        ),
    url(r'^forgot_password/sent/$',
        view=TemplateView.as_view(
            template_name="callisto_core/accounts/password_reset_sent.html",
        ),
        name='password_reset_sent',
        ),
    url(r'^reset/confirm/(?P<uidb64>.+)/(?P<token>.+)/$',
        view=auth_views.PasswordResetConfirmView.as_view(
            template_name='callisto_core/accounts/password_reset_confirm.html',
            form_class=forms.FormattedSetPasswordForm,
            success_url=reverse_lazy('login'),
        ),
        name='reset_confirm',
        ),
    url(r'^activate/(?P<uidb64>.+)/(?P<token>.+)/$',
        view=auth_views.PasswordResetConfirmView.as_view(
            template_name='callisto_core/accounts/account_activation_confirm.html',
            form_class=forms.ActivateSetPasswordForm,
            success_url=reverse_lazy('login'),
        ),
        name='activate_account',
        ),
]
