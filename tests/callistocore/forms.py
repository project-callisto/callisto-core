from django.conf import settings
from django.http import HttpResponse

from callisto.delivery.matching import CallistoMatching
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
    def send_report_to_authority(arg1, arg2, arg3):
        pass


class CustomMatchingApi(CallistoMatching):

    @classmethod
    def run_matching(cls, match_reports_to_check=None):
        super(CustomMatchingApi, cls).run_matching(match_reports_to_check)

    @classmethod
    def process_new_matches(cls, matches, identifier):
        pass
