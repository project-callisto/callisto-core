from django.conf import settings
from django.core.urlresolvers import reverse
from django.views import generic as views

from ..delivery import view_partials as delivery_view_partials
from ..utils import api


class SubmissionPartial(
    delivery_view_partials.ReportAccessView,
    views.edit.UpdateView,
):
    template_name = 'callisto_core/reporting/submission.html'

    def get_success_url(self):
        return reverse(
            self.success_url,
            kwargs={'uuid': self.report.uuid},
        )


class ReportSubclassPartial(
    SubmissionPartial,
):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': None})
        return kwargs


class MatchingPartial(
    ReportSubclassPartial,
):

    def _send_match_email(self):
        api.NotificationApi.send_confirmation(
            email_type='match_confirmation',
            to_addresses=[self.report.contact_email],
            site_id=self.site_id,
        )

    def form_valid(self, form):
        output = super().form_valid(form)
        if form.data.get('identifier'):
            self._send_match_email()
            if settings.MATCH_IMMEDIATELY:
                api.MatchingApi.run_matching(
                    match_reports_to_check=[form.instance],
                )
        return output


class ConfirmationPartial(
    ReportSubclassPartial,
):

    def _send_report_emails(self):
        for sent_full_report in self.report.sentfullreport_set.all():
            api.NotificationApi.send_report_to_authority(
                sent_report=sent_full_report,
                report_data=self.storage.decrypted_report,
                site_id=self.site_id,
            )
        api.NotificationApi.send_confirmation(
            email_type='submit_confirmation',
            to_addresses=[self.report.contact_email],
            site_id=self.site_id,
        )

    def form_valid(self, form):
        output = super().form_valid(form)
        self._send_report_emails()
        return output
