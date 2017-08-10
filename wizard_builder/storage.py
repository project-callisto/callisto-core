from django.utils.datastructures import MultiValueDict

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class SessionStorage(object):
    prefix = 'wizard'
    step_key = 'step'
    step_data_key = 'step_data'
    extra_data_key = 'extra_data'

    def __init__(self, request):
        self.request = request
        if self.prefix not in self.request.session:
            self.init_data()

    def init_data(self):
        self.data = {
            self.step_key: None,
            self.step_data_key: {},
            self.extra_data_key: {},
        }

    def _get_current_step(self):
        return self.data[self.step_key]

    def _set_current_step(self, step):
        self.data[self.step_key] = step

    @property
    def current_step(self):
        return self._get_current_step()

    @current_step.setter
    def current_step(self, value):
        return self._set_current_step(value)

    def _get_extra_data(self):
        return self.data[self.extra_data_key]

    def _set_extra_data(self, extra_data):
        self.data[self.extra_data_key] = extra_data

    @property
    def extra_data(self):
        return self._get_extra_data()

    @extra_data.setter
    def extra_data(self, value):
        return self._set_extra_data(value)

    def get_step_data(self, step):
        # When reading the serialized data, upconvert it to a MultiValueDict,
        # some serializers (json) don't preserve the type of the object.
        values = self.data[self.step_data_key].get(step, None)
        if values is not None:
            values = MultiValueDict(values)
        return values

    def set_step_data(self, step, cleaned_data):
        # If the value is a MultiValueDict, convert it to a regular dict of the
        # underlying contents.  Some serializers call the public API on it (as
        # opposed to the underlying dict methods), in which case the content
        # can be truncated (__getitem__ returns only the first item).
        if isinstance(cleaned_data, MultiValueDict):
            cleaned_data = dict(cleaned_data.lists())
        self.data[self.step_data_key][step] = cleaned_data

    @property
    def current_step_data(self):
        return self.get_step_data(self.current_step)

    def _get_data(self):
        self.request.session.modified = True
        return self.request.session[self.prefix]

    def _set_data(self, value):
        self.request.session[self.prefix] = value
        self.request.session.modified = True

    data = property(_get_data, _set_data)
