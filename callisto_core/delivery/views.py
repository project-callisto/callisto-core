'''

These views integrate thoroughly with django class based views
https://docs.djangoproject.com/en/1.11/topics/class-based-views/
an understanding of them is required to utilize the views effectively

'''
import logging

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.views import generic as views

from . import forms, view_partials

User = get_user_model()
logger = logging.getLogger(__name__)


class ReportCreateView(
    view_partials.ReportBasePartial,
    views.edit.CreateView,
):
    form_class = forms.ReportCreateForm

    def get_success_url(self):
        return reverse(
            'report_update',
            kwargs={'step': 0, 'uuid': self.object.uuid},
        )

    def form_valid(self, form):
        self._set_key_from_form(form)
        return super().form_valid(form)

    def _set_key_from_form(self, form):
        # TODO: move to _SecretKeyStorageHelper
        if form.data.get('key'):
            self.storage.set_secret_key(form.data['key'])


class ReportDeleteView(
    view_partials.ReportActionView,
):

    def view_action(self):
        print('ReportDeleteView.view_action')
        self.report.delete()
