# TODO: rename this file to api.py

from callisto_core.matching.api import CallistoCoreMatchingApi
from callisto_core.notification.api import CallistoCoreNotificationApi

from django.conf import settings
from django.contrib.sites.models import Site


class SiteAwareNotificationApi(CallistoCoreNotificationApi):

    def user_site_id(self, user):
        Site.objects.filter(id=1).update(domain='testserver')
        return 1


class SendDisabledNotificationApi(SiteAwareNotificationApi):

    def send(self):
        pass


class CustomNotificationApi(SiteAwareNotificationApi):

    from_email = '"Custom" <custom@{0}>'.format(settings.APP_URL)
    report_filename = "custom_{0}.pdf.gpg"
    report_title = 'Custom'


class ExtendedCustomNotificationApi(CustomNotificationApi):

    def send_report_to_authority(*args):
        pass


class CustomMatchingApi(CallistoCoreMatchingApi):

    def process_new_matches(*args):
        pass
