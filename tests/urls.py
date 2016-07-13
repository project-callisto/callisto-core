from django.conf.urls import url

from .views import edit_test_wizard_view, new_test_wizard_view

urlpatterns = [
    url(r'^wizard/(?P<step>.+)/$', new_test_wizard_view, name="test_wizard"),
    url(r'^wizard/edit/(?P<report_id>\d+)/(?P<step>.+)/$', edit_test_wizard_view, name='test_edit_wizard'),
]
