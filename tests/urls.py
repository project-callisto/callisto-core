from django.conf.urls import url

from .callistocore.views import edit_test_report_view, new_test_report_view

urlpatterns = [
    url(r'^test_reports/new/(?P<step>.+)/$', new_test_report_view, name="test_new_report"),
    url(r'^test_reports/edit/(?P<report_id>\d+)/$', edit_test_report_view, name='test_edit_report'),
    url(r'^test_reports/edit/(?P<report_id>\d+)/(?P<step>.+)/$', edit_test_report_view, name='test_edit_report'),
]
