'''

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/http/urls/

'''
from decorator_include import decorator_include

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import base as django_views

urlpatterns = [

    # includes
    url(r'^account/', include('callisto_core.accounts.urls')),
    url(r'^reports/', decorator_include(login_required, 'callisto_core.delivery.urls')),

    # login / signup
    url(r'^$', django_views.RedirectView.as_view(
        url=reverse_lazy('signup'))),
    url(r'^signup/$', django_views.RedirectView.as_view(
        url=reverse_lazy('signup'))),
    url(r'^logout/$', django_views.RedirectView.as_view(
        url=reverse_lazy('logout'))),
    url(r'^login/$', django_views.RedirectView.as_view(
        url=reverse_lazy('login'))),

    # admin
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^admin/', admin.site.urls),

]
