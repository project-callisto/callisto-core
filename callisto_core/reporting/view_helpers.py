'''

View helpers contain functionality shared between several view partials.
None of these classes provide full view functionality.

'''
from django.urls import reverse


class ReportingSuccessUrlMixin:
    reporting_success_url = None

    def get_reporting_success_url(self):
        return reverse(
            self.reporting_success_url,
            kwargs={'uuid': self.report.uuid},
        )

    def get_success_url(self):
        if self.reporting_success_url:
            return self.get_reporting_success_url()
        else:
            return super().get_success_url()
