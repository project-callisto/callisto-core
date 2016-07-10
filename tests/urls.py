from django.conf.urls import url

from callisto.delivery.views import (
    edit_record_form_view, new_record_form_view, submit_to_matching,
    submit_to_school, withdraw_from_matching,
)

from .callistocore.forms import (
    CustomMatchReport, CustomReport, EncryptedFormWizard,
)

urlpatterns = [
    url(r'^test_reports/new/(?P<step>.+)/$', new_record_form_view,
        {'wizard': EncryptedFormWizard}, name="test_new_report"),
    url(r'^test_reports/edit/(?P<report_id>\d+)/$', edit_record_form_view,
        {'wizard': EncryptedFormWizard, 'url_name': 'test_edit_report'}, name='test_edit_report'),
    url(r'^test_reports/edit/(?P<report_id>\d+)/(?P<step>.+)/$', edit_record_form_view,
        {'wizard': EncryptedFormWizard, 'url_name': 'test_edit_report'}, name='test_edit_report'),
    url(r'^test_reports/submit/(?P<report_id>\d+)/$', submit_to_school, name="test_submit_report"),
    url(r'^test_reports/submit_custom/(?P<report_id>\d+)/$', submit_to_school,
        {'form_template_name': 'submit_to_school_custom.html',
         'confirmation_template_name': 'submit_to_school_confirmation_custom.html',
         'report_class': CustomReport}, name="test_submit_confirmation"),
    url(r'^test_reports/match/(?P<report_id>\d+)/$', submit_to_matching, name="test_submit_match"),
    url(r'^test_reports/match_custom/(?P<report_id>\d+)/$', submit_to_matching,
        {'form_template_name': 'submit_to_matching_custom.html',
         'confirmation_template_name': 'submit_to_matching_confirmation_custom.html',
         'report_class': CustomMatchReport}, name="test_match_confirmation"),
    url(r'^test_reports/withdraw_match/(?P<report_id>\d+)/$', withdraw_from_matching,
        {'template_name': 'after_withdraw.html'}, name="test_withdraw_match"),
]
