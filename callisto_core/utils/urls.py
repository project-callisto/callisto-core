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
    # url(r'^submission/submit/(?P<report_id>\d+)/$', submit_report_to_authority, name="test_submit_report"),
    # url(r'^submission/submit_custom/(?P<report_id>\d+)/$', submit_report_to_authority,
    #     {'form_template_name': 'submit_report_to_authority_custom.html',
    #      'confirmation_template_name': 'submit_report_to_authority_confirmation_custom.html',
    #      'extra_context': {'test': 'custom context'}}, name="test_submit_confirmation"),
    # url(r'^submission/match/(?P<report_id>\d+)/$', submit_to_matching, name="test_submit_match"),
    # url(r'^submission/match_custom/(?P<report_id>\d+)/$', submit_to_matching,
    #     {'form_template_name': 'submit_to_matching_custom.html',
    #      'confirmation_template_name': 'submit_to_matching_confirmation_custom.html',
    #      'extra_context': {'test': 'custom context'}}, name="test_match_confirmation"),
    # url(r'^submission/withdraw_match/(?P<report_id>\d+)/$', withdraw_from_matching,
    #     {'template_name': 'after_withdraw.html',
    #      'extra_context': {'test': 'custom context'}}, name="test_withdraw_match"),
    # url(r'^submission/export/(?P<report_id>\d+)/$', export_as_pdf, name="test_export"),
    # url(r'^submission/export_custom/(?P<report_id>\d+)/$', export_as_pdf,
    #     {'extra_context': {'test': 'custom context'}}, name="test_export_custom"),
    # url(r'^submission/delete/(?P<report_id>\d+)/$', delete_report,
    #     {'extra_context': {'test': 'custom context'}}, name="delete_report"),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', admin.site.urls),
]
