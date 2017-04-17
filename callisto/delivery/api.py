from abc import ABCMeta, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string


class DeliveryApi(object):
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

    def __init__(self):
        self.set_api_class()

    def __getattr__(self, attr):
        if attr in AbstractNotification.__dict__.keys():
            return getattr(self.notification, attr)
        else:
            raise NotImplementedError('Attribute not implemented on abstract notification class')

    def set_api_class(self):
        override_class_path = getattr(
            settings,
            'CALLISTO_NOTIFICATION_API',
            'callisto.delivery.api.AbstractNotification',
        )
        self.notification = import_string(override_class_path)


class AbstractNotification:
    __metaclass__ = ABCMeta

    @abstractmethod
    def send_report_to_school(self):
        pass

    @abstractmethod
    def send_matching_report_to_school(self):
        pass

    @abstractmethod
    def send_user_notification(self):
        pass

    @abstractmethod
    def send_match_notification(self):
        pass

    @abstractmethod
    def send_email_to_coordinator(self):
        pass
