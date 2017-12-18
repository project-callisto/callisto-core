from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import base as django_views

# from . import views

urlpatterns = [
    # record flow
    url(r'^$',
        django_views.RedirectView.as_view(
            url=reverse_lazy('report_new'),
        ),
        name='report_index',
        ),
    # url(r'^new/$',
    #     views.ReportCreateView.as_view(
    #         success_url='report_update',
    #     ),
    #     name='report_new',
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/wizard/step/(?P<step>.+)/$',
    #     views.EncryptedWizardView.as_view(),
    #     name='report_update',
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/wizard/step/done/$',
    #     views.WizardReviewView.as_view(),
    #     name="report_view",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/review/pdf/view/$',
    #     views.ViewPDFView.as_view(),
    #     name="report_pdf_view",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/review/pdf/download/$',
    #     views.DownloadPDFView.as_view(),
    #     name="report_pdf_download",
    #     ),
    # # /end record flow
    # # review and submission flow
    # url(r'^uuid/(?P<uuid>.+)/reporting/confirmation/$',
    #     views.ReportingSchoolEmailFormView.as_view(
    #         back_url='dashboard',
    #         next_url='reporting_prep',
    #         success_url='email_confirmation_response',
    #     ),
    #     name="reporting_email_confirmation",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/reporting/confirmation/uidb64/(?P<uidb64>.+)/token/(?P<token>.+)/$',
    #     views.ReportingSchoolEmailConfirmationView.as_view(
    #         back_url='dashboard',
    #         next_url='reporting_prep',
    #     ),
    #     name="reporting_email_confirmation",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/reporting/prep/$',
    #     views.ReportingPrepView.as_view(
    #         back_url='dashboard',
    #         reporting_success_url='reporting_matching_enter',
    #     ),
    #     name="reporting_prep",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/reporting/matching/$',
    #     views.ReportingMatchingView.as_view(
    #         back_url='reporting_prep',
    #         reporting_success_url='reporting_end_step',
    #     ),
    #     name="reporting_matching_enter",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/reporting/end/$',
    #     views.ReportingConfirmationView.as_view(
    #         back_url='reporting_matching_enter',
    #         success_url=reverse_lazy('dashboard'),
    #     ),
    #     name="reporting_end_step",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/reporting/delete/$',
    #     views.ReportDeleteView.as_view(
    #         back_url='dashboard',
    #         success_url=reverse_lazy('dashboard_report_deleted'),
    #     ),
    #     name="report_delete",
    #     ),
    # # /reporting
    # url(r'^uuid/(?P<uuid>.+)/matching/confirmation/$',
    #     views.MatchingSchoolEmailFormView.as_view(
    #         back_url='dashboard',
    #         next_url='matching_prep',
    #         success_url='email_confirmation_response',
    #     ),
    #     name="matching_email_confirmation",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/matching/confirmation/uidb64/(?P<uidb64>.+)/token/(?P<token>.+)/$',
    #     views.MatchingSchoolEmailConfirmationView.as_view(
    #         back_url='dashboard',
    #         next_url='matching_prep',
    #     ),
    #     name="matching_email_confirmation",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/matching/prep/$',
    #     views.MatchingPrepView.as_view(
    #         back_url='dashboard',
    #         reporting_success_url='matching_enter',
    #     ),
    #     name="matching_prep",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/matching/enter/$',
    #     views.MatchingEnterView.as_view(
    #         back_url='matching_prep',
    #         success_url=reverse_lazy('dashboard'),
    #     ),
    #     name="matching_enter",
    #     ),
    # url(r'^uuid/(?P<uuid>.+)/matching/withdraw/$',
    #     views.MatchingWithdrawView.as_view(
    #         back_url='matching_prep',
    #         success_url=reverse_lazy('dashboard_matching_withdrawn'),
    #     ),
    #     name="matching_withdraw",
    #     ),
    # # / matching
    # # dashboard views
    # url(r'^dashboard/$',
    #     views.DashboardView.as_view(),
    #     name='dashboard',
    #     ),
    # url(r'^dashboard/report_deleted/$',
    #     views.DashboardReportDeletedView.as_view(),
    #     name='dashboard_report_deleted',
    #     ),
    # url(r'^dashboard/matching_withdrawn/$',
    #     views.DashboardMatchingWithdrawnView.as_view(),
    #     name='dashboard_matching_withdrawn',
    #     ),
    # # TODO: remove
    # url(r'^dashboard/uuid/(?P<uuid>.+)/$',
    #     django_views.RedirectView.as_view(
    #         url=reverse_lazy('dashboard'),
    #     ),
    #     name='dashboard',
    #     ),
    # url(r'^dashboard/confirmation/$',
    #     django_views.TemplateView.as_view(
    #         template_name="callisto_site/school_email_sent.html",
    #     ),
    #     name='email_confirmation_response',
    #     ),
    # # TODO: remove
    # url(r'^dashboard/confirmation/uuid/(?P<uuid>.+)/$',
    #     django_views.RedirectView.as_view(
    #         url=reverse_lazy('email_confirmation_response'),
    #     ),
    #     name='email_confirmation_response',
    #     ),
    # # / dashboard views
]
