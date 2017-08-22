from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView

from ..delivery import views as delivery_views, wizard as delivery_wizard
from ..reporting import views as reporting_views

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(url=reverse_lazy('report_new')),
        name='index',
        ),
    url(r'^reports/new/$',
        delivery_views.ReportCreateView.as_view(),
        name='report_new',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/(?P<step>.+)/$',
        delivery_wizard.EncryptedWizardView.as_view(),
        name='report_update',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/done/$',
        delivery_wizard.EncryptedWizardView.as_view(),
        name="report_view",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/pdf/$',
        delivery_wizard.WizardPDFView.as_view(),
        name="report_view_pdf",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/delete/$',
        delivery_views.ReportDeleteView.as_view(),
        name="report_delete",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/submission$',
        reporting_views.ReportingView.as_view(),
        name="report_submission",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/matching/enter/$',
        reporting_views.MatchingView.as_view(),
        name="report_matching_enter",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/matching/withdraw/$',
        reporting_views.MatchingWithdrawView.as_view(),
        name="report_matching_withdraw",
        ),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', admin.site.urls),
]
