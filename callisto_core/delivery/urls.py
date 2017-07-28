from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^(?P<uuid>.+)/details$',
        views.ReportDetail.as_view(),
        name="report_details",
    ),
]
