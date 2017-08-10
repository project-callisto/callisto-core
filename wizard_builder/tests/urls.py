from django.conf.urls import include, url
from django.contrib import admin

from .test_app import views

urlpatterns = [
    url(r'^$',
        views.TestWizardView.as_view(),
        name='wizard_view',
        ),
    url(r'^wizard/new/$',
        views.TestWizardView.as_view(),
        name='wizard_view',
        ),
    url(r'^wizard/new/(?P<step>.+)/$',
        views.TestWizardView.as_view(),
        name='wizard_view',
        ),
    url(r'^admin/', admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')),
]
