from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.NewWizardView.as_view(),
        ),
    url(r'^new/$',
        views.NewWizardView.as_view(),
        name='wizard_new',
        ),
    url(r'^step/(?P<step>.+)/$',
        views.WizardView.as_view(),
        name='wizard_update',
        ),
]
