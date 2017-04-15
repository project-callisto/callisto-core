from django.conf import settings
from django.utils.module_loading import import_string


class NotificationApi(object):

    def __init__(self):
        self.set_api_class()

    def __getattr__(self, attr):
        return getattr(self.api, attr)

    def set_api_class(self):
        override_class_path = getattr(
            settings,
            'CALLISTO_NOTIFICATION_API',
            'callisto.notification.api.NotificationApi',
        )
        self.api = import_string(override_class_path)
