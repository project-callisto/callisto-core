from abc import ABCMeta, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string


class Api(object):
    '''
        Used to route calls to from inside of callisto/delivery/* to api(s) inside of other apps

        Extending objects should have 'api_env_variable' and 'default_classpath' members.
        See DeliveryApi for an example
    '''

    def __init__(self):
        self.set_api_class(self.api_env_variable, self.default_classpath)

    def __getattr__(self, attr):
        return getattr(self.api_implementation, attr)

    def set_api_class(self, api_env_variable, default_classpath):
        override_class_path = getattr(
            settings,
            api_env_variable,
            default_classpath,
        )
        self.api_implementation = import_string(override_class_path)


class DeliveryApi(Api):
    '''
        Used to route calls to from inside of callisto/delivery/* to
        notification api(s) inside of other apps

        this object is called with
            from callisto.delivery.api import DeliveryApi
            DeliveryApi().example_call

        which maps to CALLISTO_NOTIFICATION_API
            CALLISTO_NOTIFICATION_API.example_call

        use CALLISTO_NOTIFICATION_API to override the class that
        DeliveryApi maps to
    '''

    api_env_variable = 'CALLISTO_NOTIFICATION_API'
    default_classpath = 'callisto.delivery.api.AbstractNotification'

    def __getattr__(self, attr):
        return getattr(self.api_implementation, attr, None)


class AbstractNotification:
    __metaclass__ = ABCMeta

    @abstractmethod
    def send_report_to_authority(self):
        pass

    @abstractmethod
    def send_matching_report_to_authority(self):
        pass

    @abstractmethod
    def send_user_notification(self):
        pass

    @abstractmethod
    def send_match_notification(self):
        pass

    @abstractmethod
    def send_email_to_authority_intake(self):
        pass

    @abstractmethod
    def get_user_site(self):
        pass

    # TODO: https://github.com/SexualHealthInnovations/callisto-core/issues/150
    # TODO (cont): create AbstractPDFGenerator class
    @abstractmethod
    def get_report_title(self):
        pass

    @abstractmethod
    def get_cover_page(self):
        pass
