from django.conf import settings
from django.utils.module_loading import import_string


class DeliveryNotificationApi(object):
    '''
        Used to route calls to from inside of callisto/delivery/* to
        notification api(s) inside of other apps

        this object is called with
            from callisto.delivery.api import DeliveryNotificationApi
            DeliveryNotificationApi().example_call

        which maps to (on default settings)
            from callisto.notification.api import NotificationApi
            NotificationApi.example_call

        use CALLISTO_NOTIFICATION_API to override the class that
        calls to DeliveryNotificationApi map to
    '''

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
