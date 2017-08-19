from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView

from ..delivery import views, wizard

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(url=reverse_lazy('report_new')),
        name='index',
        ),
    url(r'^reports/new/$',
        views.ReportCreateView.as_view(),
        name='report_new',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/(?P<step>.+)/$',
        wizard.EncryptedWizardView.as_view(),
        name='report_update',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/done/$',
        wizard.EncryptedWizardView.as_view(),
        name="report_view",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/pdf/$',
        wizard.WizardPDFView.as_view(),
        name="report_view_pdf",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/submission$',
        views.ReportingView.as_view(),
        name="report_submission",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/matching/enter/$',
        views.MatchingView.as_view(),
        name="report_matching_enter",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/matching/withdraw/$',
        views.MatchingWithdrawView.as_view(),
        name="report_matching_withdraw",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/delete/$',
        views.ReportDeleteView.as_view(),
        name="report_delete",
        ),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', admin.site.urls),
]
