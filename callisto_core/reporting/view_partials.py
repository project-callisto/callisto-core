from django.core.urlresolvers import reverse

from ..delivery import view_partials as delivery_view_partials


class SubmissionPartial(
    delivery_view_partials.ReportUpdateView,
):
    template_name = 'callisto_core/reporting/submission.html'

    def get_success_url(self):
        return reverse(
            self.success_url,
            kwargs={'uuid': self.report.uuid},
        )


class PrepPartial(
    SubmissionPartial,
):
    back_url = 'report_view'


class MatchingPartial(
    SubmissionPartial,
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


class ConfirmationPartial(
    SubmissionPartial,
):

    def _send_email_confirmations(self):
        pass

    def form_valid(self, form):
        output = super().form_valid(form)
        self._send_email_confirmations()
        return output

    def get_success_url(self):
        return reverse(
            'report_view',
            kwargs={'uuid': self.report.uuid},
        )
