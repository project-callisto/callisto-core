
# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView
from callisto.delivery import views


urlpatterns = [
    url(r'', TemplateView.as_view(template_name="base.html")),
    url(r'^edit/(?P<report_id>\d+)/$', views.edit_record_form_view, name='edit_report'),
]