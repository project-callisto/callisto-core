from django.contrib.sites.models import Site

from callisto_core.matching.api import CallistoCoreMatchingApi
from callisto_core.notification.api import CallistoCoreNotificationApi


class SiteAwareNotificationApi(CallistoCoreNotificationApi):

    def user_site_id(self, user):
        Site.objects.filter(id=1).update(domain='testserver')
        return 1


class SendDisabledNotificationApi(SiteAwareNotificationApi):

    def send(self):
        pass


class CustomMatchingApi(CallistoCoreMatchingApi):

    def process_new_matches(*args):
        pass
