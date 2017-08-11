from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class PageForm(forms.Form):

    @property
    def sections(self):
        from .models import Page
        return dict(Page.SECTION_CHOICES)

    @property
    def serialized(self):
        return [
            question.serialized
            for question in self.page.questions
        ]

    @classmethod
    def setup(cls, page):
        cls.base_fields = {
            question.field_id: question.make_field()
            for question in page.questions
        }
        return cls

    def _clean_data(self):
        '''
            this function exists because request.POST gives attributes as lists

            so we get ex.
                self.data['text'] = ['my text input']

            this function resolves cases like that down to
                self.data['text'] = ['my text input'][0]

            there is likely a django method that handles these cases, though
        '''
        for key, value in self.data.items():
            if (isinstance(value, list)) and (len(value) == 1):
                self.data[key] = value[0]

    def _clean_fields(self):
        for name, field in self.fields.items():
            self._clean_data()
            self.cleaned_data[name] = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name))
