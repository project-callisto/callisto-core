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

    def send_report_to_school(self, *args, **kwargs):
        return self.api.send_report_to_school(*args, **kwargs)

    def send_matching_report_to_school(self, *args, **kwargs):
        return self.api.send_matching_report_to_school(*args, **kwargs)

    def send_user_notification(self, *args, **kwargs):
        return self.api.send_user_notification(*args, **kwargs)

    def send_match_notification(self, *args, **kwargs):
        return self.api.send_match_notification(*args, **kwargs)

    def send_email_to_coordinator(self, *args, **kwargs):
        return self.api.send_email_to_coordinator(*args, **kwargs)
