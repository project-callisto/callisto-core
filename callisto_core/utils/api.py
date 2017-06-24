from abc import ABCMeta

from django.conf import settings
from django.utils.module_loading import import_string


class Api(metaclass=ABCMeta):
    '''
        Used to create overrideable calls

        Extending objects should define
            api_env_variable, ex: 'CALLISTO_EXAMPLE_API'
            default_classpath, ex: 'project.app.api.ExampleApi'
    '''

    def __init__(self):
        self.set_api_class(self.api_env_variable, self.default_classpath)

    def __getattr__(self, attr):
        return getattr(self.api_implementation, attr, None)

    def set_api_class(self, api_env_variable, default_classpath):
        override_class_path = getattr(
            settings,
            api_env_variable,
            default_classpath,
        )
        self.api_implementation = import_string(override_class_path)

class TestApi(Api):

    @classmethod
    def mew(cls):
        print('mew!!!!!')
