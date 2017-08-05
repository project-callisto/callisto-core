from django.conf.urls import include, url
from django.contrib import admin

from .test_app.views import edit_test_wizard_view, new_test_wizard_view

urlpatterns = [
    url(r'^$',
        new_test_wizard_view,
        name='index',
    ),
    url(r'^wizard/new/$',
        new_test_wizard_view,
        name='new_test_wizard',
    ),
    url(r'^wizard/new/(?P<step>.+)/$',
        new_test_wizard_view,
        name='test_wizard',
    ),
    url(r'^wizard/edit/(?P<edit_id>\d+)/(?P<step>.+)/$',
        edit_test_wizard_view,
        name='test_edit_wizard',
    ),
    url(r'^admin/', admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')),
]
