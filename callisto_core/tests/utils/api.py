from callisto_core.notification.api import CallistoCoreNotificationApi
from callisto_core.reporting.api import CallistoCoreMatchingApi

from django.contrib.sites.models import Site


class SiteAwareNotificationApi(CallistoCoreNotificationApi):

    def user_site_id(self, user):
        Site.objects.filter(id=1).update(domain='testserver')
        return 1


class CustomNotificationApi(SiteAwareNotificationApi):

    def send_email(self):
        pass  # disable sending

    def log_action(self):
        super().log_action()
        for key, value in self.context.items():
            self._logging(**{key: value})

    def _logging(self, *args, **kwargs):
        pass  # for testing inputs


class CustomMatchingApi(CallistoCoreMatchingApi):

    pass
