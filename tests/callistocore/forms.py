from django.conf import settings
from django.http import HttpResponse

from callisto.delivery.report_delivery import PDFFullReport, PDFMatchReport
from callisto.delivery.wizard import EncryptedFormBaseWizard
from callisto.notification.api import NotificationApi


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)


class CustomNotificationApi(NotificationApi):

    # TODO: https://github.com/SexualHealthInnovations/callisto-core/issues/150
    report_title = "Custom"

    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_{0}.pdf.gpg"


class CustomMatchNotificationApi(NotificationApi):

    # TODO: https://github.com/SexualHealthInnovations/callisto-core/issues/150
    report_title = "Custom"

    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_match_{0}.pdf.gpg"
