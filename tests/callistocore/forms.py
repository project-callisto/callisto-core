from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.backends.dummy import EmailBackend
from django.http import HttpResponse

from callisto.delivery.matching import CallistoMatching
from callisto.delivery.wizard import EncryptedFormBaseWizard
from callisto.notification.api import NotificationApi


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)


class SiteAwareNotificationApi(NotificationApi):

    @classmethod
    def get_user_site(cls, user):
        site = Site.objects.get(id=1)
        site.domain = 'testserver'
        site.save()
        return site


class CustomNotificationApi(SiteAwareNotificationApi):

    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_{0}.pdf.gpg"

    @classmethod
    def get_report_title(cls):
        return 'Custom'


class ExtendedCustomNotificationApi(CustomNotificationApi):

    @classmethod
    def send_report_to_authority(cls, arg2, arg3):
        pass


class CustomMatchingApi(CallistoMatching):

    @classmethod
    def run_matching(cls, match_reports_to_check=None):
        super(CustomMatchingApi, cls).run_matching(match_reports_to_check)

    @classmethod
    def process_new_matches(cls, matches, identifier):
        pass


class CustomBackendNotificationApi(CustomNotificationApi):

    @classmethod
    def get_email_connection(cls, site_id):
        return EmailBackend()
