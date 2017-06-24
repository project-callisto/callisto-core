from abc import ABCMeta

from django.conf import settings
from django.utils.module_loading import import_string


class Api(type):
    '''
        Used to create overrideable calls

        Extending objects should define
            api_env_variable, ex: 'CALLISTO_EXAMPLE_API'
            default_classpath, ex: 'project.app.api.ExampleApi'

        See NotificationApi and SiteAwareNotificationApi for examples
    '''

    def __getattr__(cls, attr):
        override_class_path = getattr(
            settings,
            cls.api_env_variable,
            cls.default_classpath,
        )
        api_class = import_string(override_class_path)
        return getattr(api_class, attr, None)
