from django.conf import settings
from django.utils.module_loading import import_string


class Api(type):
    '''
        Used to create overrideable calls

        See CallistoCoreNotificationApi and SiteAwareNotificationApi
        for examples
    '''

    def __getattr__(cls, attr):
        override_class_path = getattr(
            settings,
            cls.API_ENV_VAR,
            cls.DEFAULT_CLASS_PATH,
        )
        api_class = import_string(override_class_path)
        return getattr(api_class, attr, None)


class MatchingApi(metaclass=Api):
    API_ENV_VAR = 'CALLISTO_MATCHING_API'
    DEFAULT_CLASS_PATH = 'callisto_core.delivery.api.CallistoCoreMatchingApi'


class NotificationApi(metaclass=Api):
    API_ENV_VAR = 'CALLISTO_NOTIFICATION_API'
    DEFAULT_CLASS_PATH = 'callisto_core.notification.api.CallistoCoreNotificationApi'
