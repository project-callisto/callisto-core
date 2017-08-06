from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView

from .test_app.views import edit_test_wizard_view, new_test_wizard_view

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(url=reverse_lazy('test_wizard'), permanent=True),
    ),
    url(r'^wizard/new/$',
        RedirectView.as_view(url=reverse_lazy('test_wizard'), permanent=True),
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
