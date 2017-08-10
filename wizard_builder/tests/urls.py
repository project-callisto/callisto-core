from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView

from .test_app import views

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(
            url=reverse_lazy('wizard_view', kwargs={'step': 0})
        ),
        name='wizard_view',
        ),
    url(r'^wizard/new/$',
        RedirectView.as_view(
            url=reverse_lazy('wizard_view', kwargs={'step': 0})
        ),
        name='wizard_view',
        ),
    url(r'^wizard/new/(?P<step>.+)/$',
        views.TestWizardView.as_view(),
        name='wizard_view',
        ),
    url(r'^admin/', admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')),
]
