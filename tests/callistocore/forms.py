from django.conf import settings
from django.http import HttpResponse

from callisto.delivery.report_delivery import PDFFullReport
from callisto.delivery.wizard import EncryptedFormBaseWizard
from callisto.notification.api import NotificationApi


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)


class CustomPDFFullReport(PDFFullReport):
    report_title = "Custom"


class CustomNotificationApi(NotificationApi):
    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_{0}.pdf.gpg"


class ExtendedNotificationApi(CustomNotificationApi):
    def send_report_to_school(arg1, arg2, arg3):
        pass
