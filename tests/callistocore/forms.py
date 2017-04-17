from django.conf import settings
from django.http import HttpResponse

from callisto.delivery.wizard import EncryptedFormBaseWizard
from callisto.notification.api import NotificationApi


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)


class CustomNotificationApi(NotificationApi):

    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_{0}.pdf.gpg"

    @classmethod
    def get_report_title(self):
        return 'Custom'


class ExtendedCustomNotificationApi(CustomNotificationApi):

    @classmethod
    def send_report_to_school(arg1, arg2, arg3):
        pass
