from django.conf.urls import include, url

from callisto_core.delivery.views import (
    delete_report, edit_record_form_view, export_as_pdf, new_record_form_view,
    submit_report_to_authority, submit_to_matching, withdraw_from_matching,
)

from .callistocore.forms import EncryptedFormWizard
from callisto_core.delivery import urls as callisto_core_urls


urlpatterns = [
    url(r'^reports/', include(callisto_core_urls)),
    url(r'^test_reports/new/(?P<step>.+)/$', new_record_form_view,
        {'wizard': EncryptedFormWizard,
         'url_name': 'test_new_report'}, name="test_new_report"),
    url(r'^test_reports/edit/(?P<edit_id>\d+)/$', edit_record_form_view,
        {'wizard': EncryptedFormWizard, 'url_name': 'test_edit_report'}, name='test_edit_report'),
    url(r'^test_reports/edit/(?P<edit_id>\d+)/(?P<step>.+)/$', edit_record_form_view,
        {'wizard': EncryptedFormWizard, 'url_name': 'test_edit_report'}, name='test_edit_report'),
    url(r'^test_reports/submit/(?P<report_id>\d+)/$', submit_report_to_authority, name="test_submit_report"),
    url(r'^test_reports/submit_custom/(?P<report_id>\d+)/$', submit_report_to_authority,
        {'form_template_name': 'submit_report_to_authority_custom.html',
         'confirmation_template_name': 'submit_report_to_authority_confirmation_custom.html',
         'extra_context': {'test': 'custom context'}}, name="test_submit_confirmation"),
    url(r'^test_reports/match/(?P<report_id>\d+)/$', submit_to_matching, name="test_submit_match"),
    url(r'^test_reports/match_custom/(?P<report_id>\d+)/$', submit_to_matching,
        {'form_template_name': 'submit_to_matching_custom.html',
         'confirmation_template_name': 'submit_to_matching_confirmation_custom.html',
         'extra_context': {'test': 'custom context'}}, name="test_match_confirmation"),
    url(r'^test_reports/withdraw_match/(?P<report_id>\d+)/$', withdraw_from_matching,
        {'template_name': 'after_withdraw.html',
         'extra_context': {'test': 'custom context'}}, name="test_withdraw_match"),
    url(r'^test_reports/export/(?P<report_id>\d+)/$', export_as_pdf, name="test_export"),
    url(r'^test_reports/export_custom/(?P<report_id>\d+)/$', export_as_pdf,
        {'extra_context': {'test': 'custom context'}}, name="test_export_custom"),
    url(r'^test_reports/delete/(?P<report_id>\d+)/$', delete_report,
        {'extra_context': {'test': 'custom context'}}, name="delete_report")
]
