from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy

from callisto_core.delivery.views import (
    delete_report, export_as_pdf,
    submit_report_to_authority, submit_to_matching, withdraw_from_matching,
)
from ..delivery import wizard

urlpatterns = [
    url(r'^$',
        wizard.RedirectWizardView.as_view(),
        ),
    url(r'^new/$',
        wizard.RedirectWizardView.as_view(),
        name='wizard_new',
        ),
    url(r'^wizard/report/(?P<report_id>.+)/step/(?P<step>.+)/$',
        wizard.EncryptedWizardView.as_view(),
        name='wizard_update',
        ),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', admin.site.urls),
]
