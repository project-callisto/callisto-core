from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import base as django_views

from callisto_core.reporting import views as reporting_views

from . import views as delivery_views

urlpatterns = [
    # record flow
    url(r'^$',
        django_views.RedirectView.as_view(
            url=reverse_lazy('report_new'),
        ),
        name='report_index',
        ),
    url(r'^new/$',
        delivery_views.ReportCreateView.as_view(
            success_url='report_update',
        ),
        name='report_new',
        ),
    url(r'^uuid/(?P<uuid>.+)/wizard/step/(?P<step>.+)/$',
        delivery_views.EncryptedWizardView.as_view(),
        name='report_update',
        ),
    url(r'^uuid/(?P<uuid>.+)/wizard/step/done/$',
        delivery_views.WizardReviewView.as_view(),
        name="report_view",
        ),
    url(r'^uuid/(?P<uuid>.+)/review/pdf/view/$',
        delivery_views.ViewPDFView.as_view(),
        name="report_pdf_view",
        ),
    url(r'^uuid/(?P<uuid>.+)/review/pdf/download/$',
        delivery_views.DownloadPDFView.as_view(),
        name="report_pdf_download",
        ),
    url(r'^uuid/(?P<uuid>.+)/delete/$',
        delivery_views.ReportDeleteView.as_view(
            back_url='dashboard',
            success_url=reverse_lazy('dashboard_report_deleted'),
        ),
        name="report_delete",
        ),
    # # /end record flow
    # # review and submission flow
    url(r'^uuid/(?P<uuid>.+)/reporting/confirmation/$',
        reporting_views.ReportingSchoolEmailFormView.as_view(
            back_url='dashboard',
            next_url='reporting_prep',
            success_url='email_confirmation_response',
        ),
        name="reporting_email_confirmation",
        ),
    url(r'^uuid/(?P<uuid>.+)/reporting/confirmation/uidb64/(?P<uidb64>.+)/token/(?P<token>.+)/$',
        reporting_views.ReportingSchoolEmailConfirmationView.as_view(
            back_url='dashboard',
            next_url='reporting_prep',
        ),
        name="reporting_email_confirmation",
        ),
    url(r'^uuid/(?P<uuid>.+)/reporting/prep/$',
        reporting_views.ReportingPrepView.as_view(
            back_url='dashboard',
            reporting_success_url='reporting_matching_enter',
        ),
        name="reporting_prep",
        ),
    url(r'^uuid/(?P<uuid>.+)/reporting/matching/$',
        reporting_views.ReportingMatchingView.as_view(
            back_url='reporting_prep',
            reporting_success_url='reporting_end_step',
        ),
        name="reporting_matching_enter",
        ),
    url(r'^uuid/(?P<uuid>.+)/reporting/end/$',
        reporting_views.ReportingConfirmationView.as_view(
            back_url='reporting_matching_enter',
            success_url=reverse_lazy('dashboard'),
        ),
        name="reporting_end_step",
        ),
    # /reporting
    # matching
    url(r'^uuid/(?P<uuid>.+)/matching/confirmation/$',
        reporting_views.MatchingSchoolEmailFormView.as_view(
            back_url='dashboard',
            next_url='matching_prep',
            success_url='email_confirmation_response',
        ),
        name="matching_email_confirmation",
        ),
    url(r'^uuid/(?P<uuid>.+)/matching/confirmation/uidb64/(?P<uidb64>.+)/token/(?P<token>.+)/$',
        reporting_views.MatchingSchoolEmailConfirmationView.as_view(
            back_url='dashboard',
            next_url='matching_prep',
        ),
        name="matching_email_confirmation",
        ),
    url(r'^uuid/(?P<uuid>.+)/matching/prep/$',
        reporting_views.MatchingPrepView.as_view(
            back_url='dashboard',
            reporting_success_url='matching_enter',
        ),
        name="matching_prep",
        ),
    url(r'^uuid/(?P<uuid>.+)/matching/enter/$',
        reporting_views.MatchingEnterView.as_view(
            back_url='matching_prep',
            success_url=reverse_lazy('dashboard'),
        ),
        name="matching_enter",
        ),
    url(r'^uuid/(?P<uuid>.+)/matching/withdraw/$',
        reporting_views.MatchingWithdrawView.as_view(
            back_url='matching_prep',
            success_url=reverse_lazy('dashboard_matching_withdrawn'),
        ),
        name="matching_withdraw",
        ),
    # # / matching
    # dashboard views
    url(r'^dashboard/$',
        delivery_views.DashboardView.as_view(),
        name='dashboard',
        ),
    url(r'^dashboard/report_deleted/$',
        delivery_views.DashboardReportDeletedView.as_view(),
        name='dashboard_report_deleted',
        ),
    url(r'^dashboard/matching_withdrawn/$',
        delivery_views.DashboardMatchingWithdrawnView.as_view(),
        name='dashboard_matching_withdrawn',
        ),
    # TODO: remove
    url(r'^dashboard/uuid/(?P<uuid>.+)/$',
        django_views.RedirectView.as_view(
            url=reverse_lazy('dashboard'),
        ),
        name='dashboard',
        ),
    url(r'^dashboard/confirmation/$',
        django_views.TemplateView.as_view(
            template_name="callisto_core/accounts/school_email_sent.html",
        ),
        name='email_confirmation_response',
        ),
    # TODO: remove
    url(r'^dashboard/confirmation/uuid/(?P<uuid>.+)/$',
        django_views.RedirectView.as_view(
            url=reverse_lazy('email_confirmation_response'),
        ),
        name='email_confirmation_response',
        ),
    # / dashboard views
]
