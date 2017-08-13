from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

from .. import views

urlpatterns = [
    url(r'^$',
        views.RedirectWizardView.as_view(),
        ),
    url(r'^new/$',
        views.RedirectWizardView.as_view(),
        name='wizard_new',
        ),
    url(r'^step/(?P<step>.+)/$',
        views.WizardView.as_view(),
        name='wizard_update',
        ),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', admin.site.urls),
]
