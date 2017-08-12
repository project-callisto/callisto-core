from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^/',
        views.RedirectWizardView.as_view(),
        name='wizard_new',
        ),
    url(r'^new/',
        views.RedirectWizardView.as_view(),
        name='wizard_new',
        ),
    url(r'^step/(?P<step>.+)/',
        views.WizardView.as_view(),
        name='wizard_update',
        ),
]
