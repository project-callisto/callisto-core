from django.conf import settings
from django.utils.module_loading import import_string


class Api(type):
    '''
        Used to create overrideable calls

        See CallistoCoreNotificationApi and SiteAwareNotificationApi
        for example implementations

        By default, calls to (ex) NotificationApi will be routed to
        CallistoCoreNotificationApi. So...

            NotificationApi.example_call()

        resolves to...

            CallistoCoreNotificationApi.example_call()

        The purposes of the Api classes are to allow implementors to define
        custom functionality. So you can create an ProjectExampleApi that
        is a subclass of CallistoCoreNotificationApi and redefines all of
        its functions. You can also disable a function by overriding it and
        making it return None.

        You can also disable an api entirely by setting DEFAULT_CLASS_PATH to
        a ProjectExampleApi that defines no functions. This is useful if you
        want to disable an entire app (ex callisto_core.notification)
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
