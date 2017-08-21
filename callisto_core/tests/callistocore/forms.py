# TODO: move to callisto_core.tests.utils.api

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
