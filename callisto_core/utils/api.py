import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def log_api_func(api, func):
    func_name = getattr(func, '__name__', str(func))
    if not func_name == '<lambda>':
        logger.debug('{}.{}'.format(
            api.__class__.__name__,
            func_name,
        ))


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
            cls.API_SETTING_NAME,
            cls.DEFAULT_CLASS_PATH,
        )
        api_instance = import_string(override_class_path)()
        func = getattr(api_instance, attr, lambda: None)
        log_api_func(api_instance, func)
        return func


class MatchingApi(metaclass=Api):
    API_SETTING_NAME = 'CALLISTO_MATCHING_API'
    DEFAULT_CLASS_PATH = 'callisto_core.reporting.api.CallistoCoreMatchingApi'


class NotificationApi(metaclass=Api):
    API_SETTING_NAME = 'CALLISTO_NOTIFICATION_API'
    DEFAULT_CLASS_PATH = 'callisto_core.notification.api.CallistoCoreNotificationApi'
