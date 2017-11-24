'''

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/http/urls/

'''
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import base as django_views

from callisto_core.delivery import views as delivery_views
from callisto_core.reporting import views as reporting_views

urlpatterns = [
    url(r'^$',
        view=delivery_views.LoginView.as_view(
            success_url=reverse_lazy('report_new')
        ),
        name='index',
        ),
    url(r'^login/$', django_views.RedirectView.as_view(
        url=reverse_lazy('login'),
        permanent=True,
    ),
        name='login',
    ),
    url(r'^reports/new/$',
        delivery_views.ReportCreateView.as_view(
            success_url='report_update',
        ),
        name='report_new',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/(?P<step>.+)/$',
        delivery_views.EncryptedWizardView.as_view(),
        name='report_update',
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/wizard/step/done/$',
        delivery_views.EncryptedWizardView.as_view(),
        name="report_view",
        ),
    # dashboard
    url(r'^dashboard/$',
        delivery_views.DashboardView.as_view(),
        name="dashboard",
        ),
    url(r'^dashboard/uuid/(?P<uuid>.+)/delete/$',
        delivery_views.ReportDeleteView.as_view(
            success_url=reverse_lazy('dashboard'),
        ),
        name="report_delete",
        ),
    url(r'^dashboard/uuid/(?P<uuid>.+)/pdf/view/$',
        delivery_views.ViewPDFView.as_view(),
        name="report_pdf_view",
        ),
    url(r'^dashboard/uuid/(?P<uuid>.+)/pdf/download/$',
        delivery_views.DownloadPDFView.as_view(),
        name="report_pdf_download",
        ),
    # reporting flow
    url(r'^reports/uuid/(?P<uuid>.+)/reporting/prep/$',
        reporting_views.ReportingPrepView.as_view(
            back_url='report_view',
            reporting_success_url='reporting_matching_enter',
        ),
        name="reporting_prep",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/reporting/matching/$',
        reporting_views.ReportingMatchingView.as_view(
            back_url='reporting_prep',
            reporting_success_url='reporting_confirmation',
        ),
        name="reporting_matching_enter",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/reporting/confirmation/$',
        reporting_views.ReportingConfirmationView.as_view(
            back_url='reporting_matching_enter',
            reporting_success_url='report_view',
        ),
        name="reporting_confirmation",
        ),
    # /end reporting flow
    # matching flow
    url(r'^reports/uuid/(?P<uuid>.+)/matching/prep/$',
        reporting_views.MatchingPrepView.as_view(
            back_url='report_view',
            reporting_success_url='matching_enter',
        ),
        name="report_matching_prep",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/matching/enter/$',
        reporting_views.MatchingEnterView.as_view(
            back_url='report_matching_prep',
            reporting_success_url='report_view',
        ),
        name="matching_enter",
        ),
    url(r'^reports/uuid/(?P<uuid>.+)/review/matching/withdraw/$',
        reporting_views.MatchingWithdrawView.as_view(
            back_url='report_view',
            reporting_success_url='report_view',
        ),
        name="report_matching_withdraw",
        ),
    # /end matching flow
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^admin/', admin.site.urls),
]
