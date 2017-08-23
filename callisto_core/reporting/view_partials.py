from django.core.urlresolvers import reverse

from ..delivery import view_partials as delivery_view_partials
from ..utils import api


class BaseReportingView(
    delivery_view_partials.ReportUpdateView,
):

    def get_form_kwargs(self):
        '''
        When access is granted, this view swaps to creating
        a new Report subclass
        '''
        kwargs = super().get_form_kwargs()
        if self.access_granted:
            kwargs.update({'instance': None})
        return kwargs

    def form_valid(self, form):
        output = super().form_valid(form)
        if form.cleaned_data.get('email_confirmation') == "True":
            api.NotificationApi.send_user_notification(
                form,
                self.email_confirmation_name,
                self.site_id,
            )
        return output

    def get_success_url(self):
        return reverse(
            'report_update',
            kwargs={'step': 0, 'uuid': self.report.uuid},
        )
